Docker containers are used by all resources (Selenium, MongoDB). This is in the interest of minimizing requirements on the host machine; if it has docker, it can run the solution.


Wikipedia.py is used to:
    Imports desired from input_molecules.py
    Fetches Wikipedia data for all five molecules
    Extracts ATC codes
    Stores Table B documents in app.molecules
    Creates a unique productMolecule index
    Handles Wikipedia rate limits