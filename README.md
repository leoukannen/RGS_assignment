# General
## `Docker Containers`

Docker containers are used for all (2) resources, including:

* app -- Runs python
* MongoDB -- You didn't require a database but I found it convenient.

Why docker: to minimize requirements on the host machine. If the host has **Docker**, it can run the complete solution.

## `How to run`
### With make
* run 'make'; the 'app' container will be watched, and when it closes, mongodb will be closed
### Without make
* run `docker compose up --build -d` at the project root (where Makefile is)
* when finished (output.csv and *.png present, 'app' container closed), run `docker compose down` or `make down`

## `Role of AI assisted development`
* ChatGPT was used instead of google.com, to find sources and better understand chemical/molecule data and how to best search for these rather than their given 5 names.
* GPT 5.6 Luna: used it very generously, barely wrote anything myself, most of the time I spent on researching.

## `General notes`
* There's an extra field called consumptionData which wasn't asked for in the assignment; [molecule]-consumption.png plots it.
* Wasn't really able to procure actual tenders, actual prices, or volume in the last 12 months.

## Finding Sources
* Lots of back-and-forth with ChatGPT. 5 years ago that would've been a lot of googling.
* Three sources are used
* - [FEST](https://www.dmp.no/globalassets/documents/om-oss/distribusjon-av-legemiddeldata/fest/festfiler/fest251.zip) - see [Caching](#caching)
* - [DMP maximum prices](https://www.dmp.no/offentlig-finansiering/pris-pa-legemidler/maksimalpris)
* - statistikk-data.fhi for the (extra/unrequested) yearly consumption data

## `Trashed approaches`
* Initially was curling wikipedia to get atcCodes, before realizing FEST (https://www.dmp.no/globalassets/documents/om-oss/distribusjon-av-legemiddeldata/fest/festfiler/fest251.zip) is a much better source for those. This is not very visible in the git log because I had at some point attempted to upload a large file (fest.xml) and I had to get aggressive with the git history.

## `Skipped`
* Procuring real tenders, real volume and real prices, because I wasn't really able to find reliable sources for them, and a large amount of time had already been spent finding those resources

## `Duplication handling`
* Because no sources, single or multiple, were found for the distinct steps of furnishing the data, I did not have to deal with duplicates.

## `Recommendations/what I would do next`
* I'd work on procuring actual notices/tenders, their lifecycles and prices, their volume in the past 12m, finding sources is the hardest part.

## Cacheing
* Realistically FEST is refreshed twice a month, this implementation pulls fest.xml and maximum-prices.xlsx no more than once per 24 hours. For a real implementation I would submit to notices of update for both these sources (or at the very least download fest.xml on the 1st and 15th of every month).

# About each python-docker-src/modules/.py

Each Python file has a focused role in the pipeline:

## `input_molecules.py`

Defines the molecule names used by the search and enrichment pipeline.

## `defineMoleculeDetailsTable.py`

Defines Table A field names and the MongoDB schema validator.

## `procureLatestFest.py`

Downloads and caches the latest FEST XML source.

## `procureLatestDMP.py`

Downloads and caches the DMP maximum-price workbook.

## `populateMoleculeDetailsWithFest.py`

Reads FEST XML and creates molecule product rows in MongoDB.

## `populateMoleculeWithDMP.py`

Matches products to DMP data and fills maximum price and product fields.

## `populateConsumptionData.py`

Fetches yearly FHI consumption data and stores it in `consumptionData`.

## `main.py`

Runs the full pipeline and always writes the CSV and chart outputs.

## `export_outputs.py`

Exports Table A to CSV and creates price and consumption charts.
