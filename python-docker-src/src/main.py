import os
import time

from pymongo import ASCENDING, MongoClient

from input_molecules import desired
from modules.wikipedia import fetch_molecule


def get_database() -> MongoClient:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/app")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)

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
        database = client.get_default_database()
        collection = database["molecules"]
        collection.create_index([("productMolecule", ASCENDING)], unique=True)

        for molecule in desired:
            document = fetch_molecule(molecule)
            collection.replace_one(
                {"productMolecule": document["productMolecule"]},
                document,
                upsert=True,
            )
            print(f"Stored {document['productMolecule']}: {len(document['atcCodes'])} ATC code(s)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
while True:
    pass