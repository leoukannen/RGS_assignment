from __future__ import annotations

import argparse
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
	print(f"Wrote {len(rows)} Table A row(s) to {CSV_PATH}")


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


def write_visualizations(rows: list[dict[str, Any]]) -> None:
	OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
	for molecule in desired:
		points = [
			(milligrams(row.get("strength")), numeric_price(row.get("maxPrice")))
			for row in rows
			if str(row.get("productMolecule", "")).casefold() == molecule.casefold()
		]
		points = sorted(
			[(strength, price) for strength, price in points if strength is not None and price is not None]
		)
		figure, axis = cast(tuple[Any, Any], plt.subplots(figsize=(8, 5))) # type: ignore
		if points:
			x_values, y_values = zip(*points)
			axis.plot(x_values, y_values, marker="o")
		else:
			axis.text(0.5, 0.5, "No price data", ha="center", va="center", transform=axis.transAxes)
		axis.set_title(f"{molecule}: maximum price by strength")
		axis.set_xlabel("Strength (mg)")
		axis.set_ylabel("Maximum price")
		axis.grid(True, alpha=0.3)
		figure.tight_layout()
		figure.savefig(str(OUTPUT_DIRECTORY / f"{molecule}.png"), dpi=150)
		plt.close(figure) # type: ignore
		print(f"Wrote visualization for {molecule}")


def main() -> None:
	parser = argparse.ArgumentParser()
	mode = parser.add_mutually_exclusive_group(required=True)
	mode.add_argument("--csv-only", action="store_true")
	mode.add_argument("--visualization-only", action="store_true")
	args = parser.parse_args()
	client = get_database()
	try:
		rows = read_rows(client)
	finally:
		client.close()
	if args.csv_only:
		write_csv(rows)
	else:
		write_visualizations(rows)


if __name__ == "__main__":
	main()