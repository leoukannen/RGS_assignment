from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator
from xml.etree.ElementTree import Element, iterparse

from pymongo import MongoClient

from modules.defineMoleculeDetailsTable import MOLECULE_DETAILS_COLLECTION
from modules.input_molecules import desired


FEST_XML_PATH = Path("/app/data/fest/fest.xml")
FEST_SOURCE_URL = (
	"https://www.dmp.no/globalassets/documents/om-oss/"
	"distribusjon-av-legemiddeldata/fest/festfiler/fest251.zip"
)


def populate_molecule_details_with_fest(
	client: MongoClient[dict[str, Any]],
	fest_xml_path: Path = FEST_XML_PATH,
) -> int:
	"""Populate Table A from FEST packages matching the configured molecules."""
	desired_names = {name.casefold() for name in desired}
	strengths = _read_strengths(fest_xml_path)
	brands = _read_brands(fest_xml_path, strengths, desired_names)
	details = client.get_default_database()[MOLECULE_DETAILS_COLLECTION]
	stored = 0

	for package in _read_packages(fest_xml_path):
		brand = brands.get(package["brand_id"])
		if brand is None:
			continue
		document = _package_document(package, brand)
		details.replace_one(
			{
				"atcCode": document["atcCode"],
				"itemNumber": document["itemNumber"],
			},
			document,
			upsert=True,
		)
		stored += 1

	print(f"Stored {stored} FEST molecule detail(s)")
	return stored


def _read_strengths(path: Path) -> dict[str, dict[str, str | None]]:
	strengths: dict[str, dict[str, str | None]] = {}
	for _, element in iterparse(path, events=("end",)):
		if _local_name(element.tag) != "VirkestoffMedStyrke":
			continue
		strength_element = _child(element, "Styrke")
		strengths[_text(element, "Id")] = {
			"substance_id": _text(element, "RefVirkestoff"),
			"strength": _attribute(strength_element, "V") if strength_element is not None else None,
			"unit": _attribute(strength_element, "U") if strength_element is not None else None,
		}
		element.clear()
	return strengths


def _read_brands(
	path: Path,
	strengths: dict[str, dict[str, str | None]],
	desired_names: set[str],
) -> dict[str, dict[str, Any]]:
	substances = _read_substances(path)
	brands: dict[str, dict[str, Any]] = {}
	for _, wrapper in iterparse(path, events=("end",)):
		if _local_name(wrapper.tag) != "OppfLegemiddelMerkevare":
			continue
		brand = _child(wrapper, "LegemiddelMerkevare")
		if brand is None:
			continue
		matched_strengths = [
			strengths[_text(reference, "RefVirkestoffMedStyrke")]
			for reference in _children(brand, "SortertVirkestoffMedStyrke")
			if _text(reference, "RefVirkestoffMedStyrke") in strengths
		]
		matched_names = {
			substances.get(item["substance_id"], {}).get("english", "").casefold()
			for item in matched_strengths
		}
		if not desired_names.intersection(matched_names):
			element_id = _text(brand, "Id")
			wrapper.clear()
			continue
		product_molecule = next(
			name for name in desired_names if name in matched_names
		)
		brands[_text(brand, "Id")] = {
			"product_molecule": product_molecule,
			"product_name": _text(brand, "Varenavn"),
			"supplier": _text(_child(brand, "ProduktInfo"), "Produsent"),
			"strength": _format_strength(matched_strengths),
		}
		wrapper.clear()
	return brands


def _read_substances(path: Path) -> dict[str, dict[str, str]]:
	substances: dict[str, dict[str, str]] = {}
	for _, element in iterparse(path, events=("end",)):
		if _local_name(element.tag) == "Virkestoff":
			substances[_text(element, "Id")] = {
				"english": _text(element, "NavnEngelsk"),
				"norwegian": _text(element, "Navn"),
			}
			element.clear()
	return substances


def _read_packages(path: Path) -> Iterator[dict[str, str | None]]:
	for _, wrapper in iterparse(path, events=("end",)):
		if _local_name(wrapper.tag) != "OppfLegemiddelpakning":
			continue
		package = _child(wrapper, "Legemiddelpakning")
		info = _child(package, "Pakningsinfo") if package is not None else None
		if package is not None and info is not None:
			atc = _child(package, "Atc")
			yield {
				"brand_id": _text(info, "RefLegemiddelMerkevare"),
				"atc_code": _attribute(atc, "V") if atc is not None else None,
				"item_number": _text(package, "Varenr"),
				"pack_size": _text(info, "Pakningsstr"),
				"market_date": _text(_child(package, "Markedsforingsinfo"), "Markedsforingsdato"),
			}
		wrapper.clear()


def _package_document(package: dict[str, str | None], brand: dict[str, Any]) -> dict[str, Any]:
	return {
		"noticeId": None,
		"tenderRef": None,
		"title": None,
		"country": "NO",
		"buyer": None,
		"productMolecule": brand["product_molecule"],
		"moleculeDetected": True,
		"moleculeVariant": brand["product_molecule"],
		"detectionMethod": "FEST English substance name",
		"atcCode": package["atc_code"],
		"itemNumber": package["item_number"],
		"productName": brand["product_name"],
		"strength": brand["strength"],
		"packSize": package["pack_size"],
		"supplier": brand["supplier"],
		"maxPrice": None,
		"packSoldLast12m": None,
		"estimatedValue": None,
		"currency": "NOK",
		"noticeType": None,
		"status": None,
		"publicationDate": package["market_date"],
		"contractStart": None,
		"procedureType": None,
		"sourceDocument": "FEST 2.5.1 XML",
		"sourceUrl": FEST_SOURCE_URL,
	}


def _format_strength(strengths: list[dict[str, str | None]]) -> str | None:
	values = [
		f"{item['strength']} {item['unit']}"
		for item in strengths
		if item["strength"] and item["unit"]
	]
	return ", ".join(values) or None


def _children(element: Element | None, name: str) -> list[Element]:
	return [child for child in element or [] if _local_name(child.tag) == name]


def _child(element: Element | None, name: str) -> Element | None:
	return next(iter(_children(element, name)), None)


def _text(element: Element | None, name: str) -> str:
	child = _child(element, name)
	return "" if child is None or child.text is None else child.text.strip()


def _attribute(element: Element | None, name: str) -> str:
	return "" if element is None else element.attrib.get(name, "")


def _local_name(tag: str) -> str:
	return tag.rsplit("}", 1)[-1]