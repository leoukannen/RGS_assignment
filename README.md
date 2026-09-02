## Docker Containers

Docker containers are used for all resources, including:

* Selenium
* MongoDB

This minimizes the requirements on the host machine. If the host has **Docker**, it can run the complete solution.

## `Wikipedia.py`

`Wikipedia.py` is responsible for:

* Importing the desired molecules from `input_molecules.py`
* Fetching Wikipedia data for all five molecules
* Extracting ATC codes
* Storing **Table B** documents in `app.molecules`
* Creating a unique `productMolecule` index

