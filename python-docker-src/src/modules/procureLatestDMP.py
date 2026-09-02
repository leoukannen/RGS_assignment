from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
import tempfile
from urllib.parse import urljoin

import requests


DMP_MAXIMUM_PRICE_PAGE = (
	"https://www.dmp.no/offentlig-finansiering/pris-pa-legemidler/maksimalpris"
)
DMP_CACHE_DIR = Path(os.getenv("DMP_CACHE_DIR", "/app/data/dmp"))
DMP_FILE_NAME = "maximum-prices.xlsx"
DMP_MAX_AGE = timedelta(hours=24)


class _MaximumPriceLinkParser(HTMLParser):
	def __init__(self) -> None:
		super().__init__()
		self.links: list[str] = []
		self._in_matching_link = False

	def handle_starttag(
		self, tag: str, attrs: list[tuple[str, str | None]]
	) -> None:
		if tag != "a":
			return
		href = dict(attrs).get("href")
		if href and "legemiddelpriser" in href.lower() and href.lower().endswith(".xlsx"):
			self.links.append(href)


def download_latest_dmp() -> Path:
	"""Download the current DMP maximum-price workbook once per 24 hours."""
	DMP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
	workbook_path = DMP_CACHE_DIR / DMP_FILE_NAME

	if _is_fresh(workbook_path):
		print(f"Using cached DMP maximum-price workbook: {workbook_path}")
		return workbook_path

	download_url = _find_workbook_url()
	with tempfile.TemporaryDirectory(dir=DMP_CACHE_DIR) as temporary_directory:
		temporary_workbook = Path(temporary_directory) / DMP_FILE_NAME
		_download(download_url, temporary_workbook)
		temporary_workbook.replace(workbook_path)

	print(f"Downloaded DMP maximum-price workbook: {workbook_path}")
	return workbook_path


def _find_workbook_url() -> str:
	response = requests.get(
		DMP_MAXIMUM_PRICE_PAGE,
		headers={"User-Agent": "assignmentCGS/1.0 (DMP data collection)"},
		timeout=30,
	)
	response.raise_for_status()
	parser = _MaximumPriceLinkParser()
	parser.feed(response.text)
	if not parser.links:
		raise ValueError("DMP maximum-price page contains no workbook link")
	return urljoin(DMP_MAXIMUM_PRICE_PAGE, parser.links[0])


def _is_fresh(path: Path) -> bool:
	if not path.is_file():
		return False
	modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
	return datetime.now(timezone.utc) - modified_at < DMP_MAX_AGE


def _download(url: str, destination: Path) -> None:
	with requests.get(
		url,
		headers={"User-Agent": "assignmentCGS/1.0 (DMP data collection)"},
		stream=True,
		timeout=120,
	) as response:
		response.raise_for_status()
		with destination.open("wb") as output:
			for chunk in response.iter_content(chunk_size=1024 * 1024):
				if chunk:
					output.write(chunk)