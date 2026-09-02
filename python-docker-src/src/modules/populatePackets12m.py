from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import time
from typing import Any, cast

import requests
from pymongo import MongoClient

from modules.defineMoleculeDetailsTable import MOLECULE_DETAILS_COLLECTION


FHI_API_ROOT = "https://statistikk-data.fhi.no/api/open/v1"
FHI_SOURCE_ID = "gs"
FHI_TABLE_TITLE = "Grossistbasert legemiddelstatistikk"
FHI_SOURCE_URL = "https://statistikk-data.fhi.no/swagger/index.html"
YEARS_BACK_TO_REQUEST = 3
REQUEST_DELAY_SECONDS = 1
MAX_RETRIES_PER_ENDPOINT = 5
MAX_BACKOFF_SECONDS = 10
WARNINGS_LOG_PATH = Path(
	os.getenv("WARNINGS_LOG_PATH", "/app/data/errors/warnings.log")
)


def populate_packets_12m(
	client: MongoClient[dict[str, Any]],
	) -> int:
	"""Add the latest available yearly GS sales measure to Table A records."""
	collection = client.get_default_database()[MOLECULE_DETAILS_COLLECTION]
	atc_codes = sorted(
		{
			document["atcCode"]
			for document in collection.find({}, {"atcCode": 1})
			if document.get("atcCode")
		}
	)
	if not atc_codes:
		return 0

	source = _get_source()
	if source.get("id") != FHI_SOURCE_ID:
		raise ValueError("FHI GS source was not found")
	table_id = _find_sales_table()
	dimensions = _get_dimensions(table_id)
	if "Varenummer" in {str(item.get("label")) for item in dimensions}:
		print("FHI exposes Varenummer, but the current query uses ATC aggregation")
	else:
		print("FHI GS table has no Varenummer dimension; using yearly ATC data")
	years = _requested_years(dimensions)
	measure = _measure_value(dimensions)
	data = _query(table_id, atc_codes, years, measure)
	packet_measure = _packet_measure_value(dimensions)
	packet_data = (
		_query(table_id, atc_codes, years, packet_measure)
		if packet_measure is not None
		else {}
	)

	updated = 0
	for (atc_code, year), value in data.items():
		if value is None:
			continue
		consumptionData_entry: dict[str, Any] = {
			"year": year,
			"atcCode": atc_code,
			"measure": measure,
			"value": value,
			"packetsSold": packet_data.get((atc_code, year)),
			"unit": "DDD",
			"periodBasis": "calendar year",
		}
		result = collection.update_many(
			{"atcCode": atc_code},
			[
				{
					"$set": {
						"consumptionData": {
							"$concatArrays": [
								{
									"$filter": {
										"input": {"$cond": [
											{"$isArray": "$consumptionData"}, "$consumptionData", []
										]},
										"as": "entry",
										"cond": {
											"$or": [
												{"$ne": ["$$entry.year", year]},
												{"$ne": ["$$entry.atcCode", atc_code]},
											],
										},
									}
								},
								[consumptionData_entry],
							]
						},
						"sourceDocument": {"$setUnion": [
							{"$cond": [{"$isArray": "$sourceDocument"}, "$sourceDocument", []]},
							["FHI Grossistbasert legemiddelstatistikk"],
						]},
						"sourceUrl": {"$setUnion": [
							{"$cond": [{"$isArray": "$sourceUrl"}, "$sourceUrl", []]},
							[FHI_SOURCE_URL],
						]},
					}
				}
			],
		)
		updated += result.modified_count

	print(f"Updated {updated} molecule detail(s) with FHI yearly data")
	return updated


def _get_source() -> dict[str, Any]:
	sources = cast(list[dict[str, Any]], _get("/Common/source"))
	empty_source: dict[str, Any] = {}
	return next(
		(source for source in sources if source.get("id") == FHI_SOURCE_ID),
		empty_source,
	)


def _find_sales_table() -> int:
	for table in _get(f"/{FHI_SOURCE_ID}/Table"):
		if FHI_TABLE_TITLE.casefold() in str(table.get("title", "")).casefold():
			return int(table["tableId"])
	raise ValueError("FHI GS sales table was not found")


def _get_dimensions(table_id: int) -> list[dict[str, Any]]:
	return _get(f"/{FHI_SOURCE_ID}/Table/{table_id}/dimension")["dimensions"]


def _requested_years(dimensions: list[dict[str, Any]]) -> list[str]:
	year_dimension = next(item for item in dimensions if item["code"] == "Salg_Ar")
	years = sorted(
		(str(category["value"]) for category in year_dimension["categories"]),
		reverse=True,
	)
	return years[:YEARS_BACK_TO_REQUEST]


def _measure_value(dimensions: list[dict[str, Any]]) -> str:
	measure_dimension = next(item for item in dimensions if item["code"] == "MEASURE_TYPE")
	values = [str(category["value"]) for category in measure_dimension["categories"]]
	return "DDD" if "DDD" in values else values[0]


def _packet_measure_value(dimensions: list[dict[str, Any]]) -> str | None:
	measure_dimension = next(item for item in dimensions if item["code"] == "MEASURE_TYPE")
	for category in measure_dimension["categories"]:
		label = str(category.get("label", "")).casefold()
		if "pakning" in label or "pakke" in label or "package" in label:
			return str(category["value"])
	return None


def _query(
	table_id: int,
	atc_codes: list[str],
	years: list[str],
	measure: str,
) -> dict[tuple[str, str], Any]:
	payload: dict[str, Any] = {
		"dimensions": [
			{"code": "ATC_Verdi", "filter": "item", "values": atc_codes},
			{"code": "Salg_Ar", "filter": "item", "values": years},
			{"code": "MEASURE_TYPE", "filter": "item", "values": [measure]},
		],
		"response": {"format": "json-stat2", "maxRowCount": 10000},
	}
	response = _request(
		"POST",
		f"{FHI_SOURCE_ID}/Table/{table_id}/data",
		json=payload,
	)
	response.raise_for_status()
	result = response.json()
	atc_values = _ordered_dimension_values(result, "ATC_Verdi")
	year_values = _ordered_dimension_values(result, "Salg_Ar")
	values: list[Any] = result.get("value", [])
	return {
		(atc_code, year): value
		for index, value in enumerate(values)
		if value != "-"
		for atc_code, year in [_coordinates(index, atc_values, year_values)]
	}


def _ordered_dimension_values(result: dict[str, Any], code: str) -> list[str]:
	category_values = cast(
		dict[str, int] | list[str],
		result["dimension"][code]["category"]["index"],
	)
	if isinstance(category_values, dict):
		return [
			value
			for value, _ in sorted(category_values.items(), key=lambda item: item[1])
		]
	return category_values


def _coordinates(index: int, atc_values: list[str], year_values: list[str]) -> tuple[str, str]:
	year_index = index % len(year_values)
	atc_index = (index // len(year_values)) % len(atc_values)
	return atc_values[atc_index], year_values[year_index]


def _get(path: str) -> Any:
	response = _request("GET", path)
	response.raise_for_status()
	return response.json()


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
	url = f"{FHI_API_ROOT}{path if path.startswith('/') else f'/{path}'}"
	kwargs.setdefault("headers", {"User-Agent": "assignmentCGS/1.0 (FHI data collection)"})
	kwargs.setdefault("timeout", 60)
	last_error: Exception | None = None

	for attempt in range(MAX_RETRIES_PER_ENDPOINT + 1):
		time.sleep(REQUEST_DELAY_SECONDS)
		try:
			response = requests.request(method, url, **kwargs)
			if not _retryable_status(response.status_code):
				return response
			last_error = requests.HTTPError(
				f"retryable HTTP status {response.status_code}", response=response
			)
		except (requests.Timeout, requests.ConnectionError) as error:
			last_error = error

		if attempt < MAX_RETRIES_PER_ENDPOINT:
			time.sleep(min(REQUEST_DELAY_SECONDS * (2**attempt), MAX_BACKOFF_SECONDS))

	message = _warning_message(method, url, last_error)
	print(message, flush=True)
	_write_warning(message)
	if last_error is not None:
		raise last_error
	raise RuntimeError(f"FHI request failed: {method} {url}")


def _retryable_status(status_code: int) -> bool:
	return status_code == 429 or status_code >= 500


def _warning_message(method: str, url: str, error: Exception | None) -> str:
	timestamp = datetime.now(timezone.utc).isoformat()
	return (
		"\n"
		"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
		f"WARNING: FHI endpoint failed after {MAX_RETRIES_PER_ENDPOINT} retries\n"
		f"Time: {timestamp}\n"
		f"Request: {method} {url}\n"
		f"Error: {error}\n"
		"The endpoint was skipped after reaching its retry limit.\n"
		"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	)


def _write_warning(message: str) -> None:
	WARNINGS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
	with WARNINGS_LOG_PATH.open("a", encoding="utf-8") as log_file:
		log_file.write(f"{message}\n")