## Docker Containers

Docker containers are used for all (2) resources, including:

* Python executions
* MongoDB

This minimizes the requirements on the host machine. If the host has **Docker**, it can run the complete solution.

## `input_molecules.py`

is responsible for:

* Defining the molecules to be searched

## `defineMoleculeDetailsTable.py`

is responsible for:

* Defining the table to be populated

## `procureLatestFest.py`

is responsible for:

* Downloading fest.xml, no more than once per day. (This would be improved with a subscription to the maintainers, which may agree to inform whenever the file changes.)

## `populateMoleculeDetailsWithFest.py`

is responsible for:

* Looking up within the downloaded fest.xml the data to be persisted in the table created by  `defineMoleculeDetailsTable.py`

## `General notes`
The database container remains running indefinately after make. There isn't a real need for that beyond being able to query it. Querying it occurs at any point and is required for producing output.csv as well as the 5 visualizations, could be set up to close cleanly after those 6 files are made.