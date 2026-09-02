from typing import Any

from pymongo import MongoClient


MOLECULE_DETAILS_COLLECTION = "moleculeDetails"
MOLECULE_DETAILS_FIELDS = (
	"noticeId",
	"tenderRef",
	"title",
	"country",
	"buyer",
	"productMolecule",
	"moleculeDetected",
	"moleculeVariant",
	"detectionMethod",
	"atcCode",
	"itemNumber",
	"productName",
	"strength",
	"packSize",
	"supplier",
	"maxPrice",
	"packSoldLast12m",
	"estimatedValue",
	"currency",
	"noticeType",
	"status",
	"publicationDate",
	"contractStart",
	"procedureType",
	"sourceDocument",
	"sourceUrl",
)


def define_molecule_details_table(
	client: MongoClient[dict[str, Any]],
) -> None:
	"""Create or update the Table A-shaped MongoDB collection."""
	database = client.get_default_database()
	validator :dict[str, Any] = {
		"$jsonSchema": {
			"bsonType": "object",
			"properties": {
				**{
					field: {"bsonType": ["string", "null"]}
					for field in MOLECULE_DETAILS_FIELDS
				},
				"moleculeDetected": {"bsonType": ["bool", "null"]},
				"sourceDocument": {
					"bsonType": ["array", "null"],
					"items": {"bsonType": "string"},
				},
				"sourceUrl": {
					"bsonType": ["array", "null"],
					"items": {"bsonType": "string"},
				},
			}
		}
	}

	if MOLECULE_DETAILS_COLLECTION not in database.list_collection_names():
		database.create_collection(
			MOLECULE_DETAILS_COLLECTION,
			validator=validator,
			validationLevel="moderate",
		)
	else:
		database.command(
			"collMod",
			MOLECULE_DETAILS_COLLECTION,
			validator=validator,
			validationLevel="moderate",
		)