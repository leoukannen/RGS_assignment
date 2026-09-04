from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pymongo import MongoClient

from modules.defineMoleculeDetailsTable import MOLECULE_DETAILS_COLLECTION


DATE_FIELDS = ("publicationDate", "contractStart")


def normalize_iso_date(value: Any) -> str | None:
	"""Convert a supported date value to ISO YYYY-MM-DD or reject it."""
	if value is None or value == "":
		return None
	if isinstance(value, datetime):
		return value.date().isoformat()
	if isinstance(value, date):
		return value.isoformat()
	if not isinstance(value, str):
		raise ValueError(f"Unsupported date value: {value!r}")

	cleaned = value.strip()
	if not cleaned:
		return None
	for date_format in ("%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
		try:
			return datetime.strptime(cleaned, date_format).date().isoformat()
		except ValueError:
			continue
	try:
		return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).date().isoformat()
	except ValueError as error:
		raise ValueError(f"Unsupported date value: {value!r}") from error


def normalize_table_dates(client: MongoClient[dict[str, Any]]) -> int:
	"""Normalize all Table A date fields already stored in MongoDB."""
	collection = client.get_default_database()[MOLECULE_DETAILS_COLLECTION]
	updated = 0
	for document in collection.find({}, {field: 1 for field in DATE_FIELDS}):
		updates = {
			field: normalized
			for field in DATE_FIELDS
			if (normalized := normalize_iso_date(document.get(field))) != document.get(field)
		}
		if updates:
			collection.update_one({"_id": document["_id"]}, {"$set": updates})
			updated += 1
	return updated
