import re
import time
from typing import Any

import requests


WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
ATC_CODE_PATTERN = re.compile(r"\b[A-Z]\d{2}[A-Z]{2}\d{2}\b")


def fetch_molecule(molecule: str) -> dict[str, Any]:
	params = {
		"action": "parse",
		"page": molecule,
		"prop": "wikitext",
		"format": "json",
		"formatversion": "2",
		"redirects": "1",
	}
	headers = {"User-Agent": "assignmentCGS/1.0 (Wikipedia data collection)"}
	response: requests.Response | None = None
	for attempt in range(3):
		response = requests.get(
			WIKIPEDIA_API_URL, params=params, headers=headers, timeout=20
		)
		if response.status_code != 429 or attempt == 2:
			break
		retry_after = int(response.headers.get("Retry-After", "2"))
		time.sleep(min(retry_after, 10))
	assert response is not None
	response.raise_for_status()
	payload = response.json()

	if "error" in payload:
		raise ValueError(f"Wikipedia page not found for {molecule!r}")

	parsed = payload["parse"]
	wikitext = parsed["wikitext"]
	atc_codes = sorted(set(_atc_codes(wikitext)))

	return {
		"productMolecule": parsed["title"],
		"atcCodes": [
			{"atcCode": code, "startPeriod": None, "endPeriod": None}
			for code in atc_codes
		],
	}


def _atc_codes(wikitext: str) -> list[str]:
	fields: dict[str, str] = dict(
		re.findall(
			r"^\s*\|\s*(ATC_(?:prefix|suffix|supplemental))\s*=\s*(.*?)\s*$",
			wikitext,
			flags=re.MULTILINE | re.IGNORECASE,
		)
	)
	codes: list[str] = []
	prefix = fields.get("ATC_prefix", "")
	suffix = fields.get("ATC_suffix", "")
	codes.extend(ATC_CODE_PATTERN.findall(prefix + suffix))
	codes.extend(ATC_CODE_PATTERN.findall(fields.get("ATC_supplemental", "")))
	return codes
