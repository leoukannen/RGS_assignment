from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymongo import MongoClient

from modules.defineMoleculeDetailsTable import (
	MOLECULE_DETAILS_COLLECTION,
	MOLECULE_DETAILS_FIELDS,
)
from modules.input_molecules import desired


OUTPUT_DIRECTORY = Path(os.getenv("OUTPUT_DIRECTORY", "/app/data/output"))
CSV_PATH = OUTPUT_DIRECTORY / "output.csv"
PRICE_FIELDS = ("maxPrice", "packSoldLast12m", "estimatedValue", "currency")
ARRAY_FIELDS = ("consumptionData", "sourceDocument", "sourceUrl")
STRENGTH_PATTERN = re.compile(
	r"(?P<amount>\d+(?:[.,]\d+)?)\s*(?P<unit>mg|g|mcg|µg|ug)\b",
	re.IGNORECASE,
)


def get_database() -> MongoClient[dict[str, Any]]:
	client: MongoClient[dict[str, Any]] = MongoClient(
		os.getenv("MONGO_URI", "mongodb://localhost:27017/app"),
		serverSelectionTimeoutMS=5000,
	)
	client.admin.command("ping")
	return client


def read_rows(client: MongoClient[dict[str, Any]]) -> list[dict[str, Any]]:
	collection = client.get_default_database()[MOLECULE_DETAILS_COLLECTION]
	return list(collection.find({}, {"_id": False}).sort("productMolecule", 1))


def csv_fields() -> tuple[str, ...]:
	leading = tuple(
		field
		for field in MOLECULE_DETAILS_FIELDS
		if field not in PRICE_FIELDS and field not in ARRAY_FIELDS
	)
	return leading + PRICE_FIELDS + ARRAY_FIELDS


def csv_value(value: Any) -> Any:
	if isinstance(value, (list, dict)):
		return json.dumps(value, ensure_ascii=True, sort_keys=True)
	return value


def write_csv(rows: list[dict[str, Any]]) -> None:
	OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
	fields = csv_fields()
	with CSV_PATH.open("w", newline="", encoding="utf-8") as output:
		writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
		writer.writeheader()
		for row in rows:
			writer.writerow({field: csv_value(row.get(field)) for field in fields})
	print(f"Wrote {len(rows)} moleculeDetails row(s) to {CSV_PATH}")


def milligrams(strength: Any) -> float | None:
	if strength is None:
		return None
	match = STRENGTH_PATTERN.search(str(strength).replace(",", "."))
	if match is None:
		return None
	amount = float(match.group("amount"))
	unit = match.group("unit").casefold()
	if unit == "g":
		return amount * 1000
	if unit in {"mcg", "ug", "µg"}:
		return amount / 1000
	return amount


def numeric_price(value: Any) -> float | None:
	if value is None:
		return None
	match = re.search(r"\d+(?:[.,]\d+)?", str(value).replace(" ", ""))
	return float(match.group(0).replace(",", ".")) if match else None


def numeric_value(value: Any) -> float | None:
	if isinstance(value, (int, float)) and not isinstance(value, bool):
		return float(value)
	return numeric_price(value)


def write_consumption_visualization(
	molecule: str,
	rows: list[dict[str, Any]],
) -> None:
	unique_entries: set[tuple[str, str, float, str]] = set()
	for row in rows:
		if str(row.get("productMolecule", "")).casefold() != molecule.casefold():
			continue
		consumption_data = row.get("consumptionData")
		if not isinstance(consumption_data, list):
			continue
		consumption_data = cast(list[Any], consumption_data)
		for entry in consumption_data:
			if not isinstance(entry, dict):
				continue
			entry = cast(dict[str, Any], entry)
			year = str(entry.get("year", "")).strip()
			atc_code = str(entry.get("atcCode", "")).strip()
			value = numeric_value(entry.get("value"))
			unit = str(entry.get("unit") or entry.get("measure") or "").strip()
			if year and atc_code and value is not None:
				unique_entries.add((year, atc_code, value, unit))

	by_year: dict[str, float] = {}
	units: set[str] = set()
	for year, _, value, unit in unique_entries:
		by_year[year] = by_year.get(year, 0) + value
		if unit:
			units.add(unit)

	figure, axis = cast(tuple[Any, Any], plt.subplots(figsize=(8, 5))) # type: ignore
	if by_year:
		years = sorted(by_year)
		axis.plot(years, [by_year[year] for year in years], marker="o")
	else:
		axis.text(0.5, 0.5, "No consumption data", ha="center", va="center", transform=axis.transAxes)
	unit_label = ", ".join(sorted(units)) or "unknown unit"
	axis.set_title(f"{molecule}: yearly consumption ({unit_label})")
	axis.set_xlabel("Year")
	axis.set_ylabel(f"Consumption ({unit_label})")
	axis.grid(True, alpha=0.3)
	figure.tight_layout()
	figure.savefig(str(OUTPUT_DIRECTORY / f"{molecule}-consumption.png"), dpi=150)
	plt.close(figure) # type: ignore
	print(f"Wrote consumption visualization for {molecule}")


def write_visualizations(rows: list[dict[str, Any]]) -> None:
	OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
	for molecule in desired:
		points: list[tuple[float, float, str, float]] = []
		for row in rows:
			if str(row.get("productMolecule", "")).casefold() != molecule.casefold():
				continue
			strength = milligrams(row.get("strength"))
			price = numeric_price(row.get("maxPrice"))
			if strength is None or strength <= 0 or price is None:
				continue
			label = str(row.get("itemNumber") or row.get("productName") or "unknown")
			points.append((strength, price, label, price / strength))
		points.sort(key=lambda point: point[0])
		figure, axis = cast(tuple[Any, Any], plt.subplots(figsize=(8, 5))) # type: ignore
		if points:
			x_values = [point[0] for point in points]
			prices = [point[1] for point in points]
			normalized_prices = [point[3] for point in points]
			axis.plot(x_values, prices, marker="o", label="Maximum price")
			axis.plot(
				x_values,
				normalized_prices,
				marker="o",
				label="Price per mg",
			)
			for index, (strength, price, label, normalized_price) in enumerate(points):
				vertical_offset = (index % 4) * 12
				axis.annotate(
					label,
					(strength, price),
					xytext=(4, 8 + vertical_offset),
					textcoords="offset points",
				)
				axis.annotate(
					label,
					(strength, normalized_price),
					xytext=(4, -16 - vertical_offset),
					textcoords="offset points",
				)
		else:
			axis.text(0.5, 0.5, "No price data", ha="center", va="center", transform=axis.transAxes)
		axis.set_title(f"{molecule}: maxPrice(FEST) by strength")
		axis.set_xlabel("Strength (mg)")
		axis.set_ylabel("Price (NOK)")
		axis.legend()
		axis.grid(True, alpha=0.3)
		figure.tight_layout()
		figure.savefig(str(OUTPUT_DIRECTORY / f"{molecule}.png"), dpi=150)
		plt.close(figure) # type: ignore
		print(f"Wrote visualization for {molecule}")
		write_consumption_visualization(molecule, rows)


def main() -> None:
	client = get_database()
	try:
		rows = read_rows(client)
	finally:
		client.close()
	write_csv(rows)
	write_visualizations(rows)


if __name__ == "__main__":
	main()