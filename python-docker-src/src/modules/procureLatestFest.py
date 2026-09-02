from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from zipfile import ZipFile

import requests


FEST_DOWNLOAD_URL = os.getenv(
	"FEST_DOWNLOAD_URL",
	"https://www.dmp.no/globalassets/documents/om-oss/distribusjon-av-legemiddeldata/fest/festfiler/fest251.zip",
)
FEST_CACHE_DIR = Path(os.getenv("FEST_CACHE_DIR", "/app/data/fest"))
FEST_XML_NAME = "fest.xml"
FEST_MAX_AGE = timedelta(hours=24)


def download_latest_fest() -> Path:
	"""Download and extract FEST once per 24 hours, returning the XML path."""
	FEST_CACHE_DIR.mkdir(parents=True, exist_ok=True)
	xml_path = FEST_CACHE_DIR / FEST_XML_NAME

	if _is_fresh(xml_path):
		print(f"Using cached FEST XML: {xml_path}")
		return xml_path

	with tempfile.TemporaryDirectory(dir=FEST_CACHE_DIR) as temporary_directory:
		temporary_zip = Path(temporary_directory) / "fest.zip"
		_download(FEST_DOWNLOAD_URL, temporary_zip)
		extracted_xml = _extract_xml(temporary_zip, Path(temporary_directory))
		temporary_xml = FEST_CACHE_DIR / f".{FEST_XML_NAME}.tmp"
		temporary_xml.write_bytes(extracted_xml.read_bytes())
		temporary_xml.replace(xml_path)

	print(f"Downloaded FEST XML: {xml_path}")
	return xml_path


def _is_fresh(path: Path) -> bool:
	if not path.is_file():
		return False
	modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
	return datetime.now(timezone.utc) - modified_at < FEST_MAX_AGE


def _download(url: str, destination: Path) -> None:
	with requests.get(
		url,
		headers={"User-Agent": "assignmentCGS/1.0 (FEST data collection)"},
		stream=True,
		timeout=120,
	) as response:
		response.raise_for_status()
		with destination.open("wb") as output:
			for chunk in response.iter_content(chunk_size=1024 * 1024):
				if chunk:
					output.write(chunk)


def _extract_xml(archive: Path, destination: Path) -> Path:
	with ZipFile(archive) as zip_file:
		xml_members = [
			member
			for member in zip_file.infolist()
			if not member.is_dir() and member.filename.lower().endswith(".xml")
		]
		if not xml_members:
			raise ValueError("FEST archive does not contain an XML file")
		member = max(xml_members, key=lambda item: item.file_size)
		extracted_path = destination / "extracted.xml"
		with zip_file.open(member) as source, extracted_path.open("wb") as output:
			output.write(source.read())
		return extracted_path
