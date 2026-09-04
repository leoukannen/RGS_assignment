from modules.procureLatestFest import download_latest_fest
from modules.procureLatestDMP import download_latest_dmp
from modules.defineMoleculeDetailsTable import define_molecule_details_table
from modules.populateMoleculeDetailsWithFest import populate_molecule_details_with_fest
from modules.populateMoleculeWithDMP import populate_molecule_with_dmp
from modules.populateConsumptionData import populate_consumption_data
from export_outputs import read_rows, write_csv, write_visualizations
from typing import Any
from pymongo import  MongoClient
import os
import time

def get_database() -> MongoClient[dict[str, Any]]:
	mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/app")
	client: MongoClient[dict[str, Any]] = MongoClient(
		mongo_uri, serverSelectionTimeoutMS=2000
	)

	for attempt in range(15):
		try:
			client.admin.command("ping")
			return client
		except Exception:
			if attempt == 14:
				client.close()
				raise
			time.sleep(2)

	raise RuntimeError("MongoDB did not become available")

def main() -> None:
	client = get_database()
	try:
		download_latest_fest()
		download_latest_dmp()
		define_molecule_details_table(client)
		populate_molecule_details_with_fest(client)
		populate_molecule_with_dmp(client)
		populate_consumption_data(client)
		rows = read_rows(client)
		write_csv(rows)
		write_visualizations(rows)
	finally:
		client.close()

if __name__ == "__main__":
    main()