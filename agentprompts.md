# Assignment Prompts

This file records the user prompts that shaped the implementation of this assignment, in chronological order.

## 1. Initial molecule lookup

> Have `main` import `desired: list[str]` from `input_molecules.py`. Visit Wikipedia for each configured molecule, use the information described in `AGENTS_README.md`, and store the results in MongoDB after provisioning the table.

## 2. Development environment target

> Define a target that installs the Python container requirements from `python-docker-src/requirements.txt` for development type completion.

## 3. Create a virtual environment

> Make sure a Python virtual environment is created and assume the IDE can use it.

## 4. Resolve Docker MongoDB addressing

> Is `localhost:27017/` necessary everywhere?

## 5. Separate the initial Norwegian-site workflow

> Move most of `main` into `wikipedia.py`, let it populate the `molecules` table, keep `main` slim, and have `main` call `norwegiansite1.py` to retrieve documents from that table.

## 6. Define Table A and inspect Norwegian medicine data

> Use the Legemiddelsøk ATC-code URL as an example, rename `retrieve_molecules` if appropriate, create `defineMoleculeDetailsTable.py` from the Table A shape in `AGENTS_README.md`, and inspect the Norwegian site response to populate the existing table.

## 7. Restart from a clean FEST-based pipeline

> Start the Python container from zero. Download the FEST XML source from DMP, and do not download it more than once per 24 hours.

## 8. Populate Table A from FEST

> Add a module that reads `data/fest/fest.xml`, uses the molecule names in `input_molecules.py`, and populates the table created by `define_molecule_details_table`.

## 9. Reorganize source modules

> Reorganize `src` so most scripts are under `modules/`.

## 10. Download DMP maximum prices

> Create `procureLatestDMP.py` to download the DMP maximum-price workbook.

## 11. Populate DMP fields

> Create `populateMoleculeWithDMP.py` to read Table A and fill its NULL fields from the downloaded `.xlsx` data.

## 12. Normalize source provenance fields

> Make `sourceDocument` and `sourceUrl` arrays of strings. When DMP supplements a molecule row, append those sources only if they are not already present.

## 13. Add FHI consumption data

> Use the FHI API at `https://statistikk-data.fhi.no/swagger/index.html` to implement `populatePackets12m.py`: find the GS source, locate sales/package tables, inspect dimensions, determine whether `Varenummer` is exposed, and query using FEST item numbers. Account for yearly rather than arbitrary monthly data and keep pricing and molecule data reasonably separate.

## 14. Add packet totals to consumption entries

> Expand each consumption entry to include total packets sold for its period basis.

## 15. Request multiple years

> The current implementation only populates 2025. Add a variable such as `YEARS_BACK_TO_REQUEST`, set to 3, and request that many years.

## 16. Fix the clean-start Make workflow

> After `full-clean-remove-volumes` followed by `all`, the workflow currently has to be run twice. Make MongoDB a dependency of `app` so Python starts second, and verify that this fixes the issue.

## 17. Add request throttling and retries

> Respect the source service: wait one second between requests, use exponential backoff up to ten seconds after timeout or retry failures, allow at most five retries per endpoint, print a prominent warning visible in Docker logs, and write warnings to `data/errors/warnings.log`.

## 18. Initial output targets and visualizations

> Add a new Makefile target called `output-files`, which calls `output-csv` and `output-visualization`.
>
> Each output target should wait until the container named `app` is no longer running. `output-csv` should export one line per Table A row, with pricing fields and array fields as the final columns. `output-visualization` should create five charts, one line chart per molecule from `input_molecules.py`, plotting `maxPrice` over milligrams.

## 19. Generate visualizations during the app run

> Change the implementation so visualizations are created by `main.py` after all previous processing completes, instead of launching `app` separately for visualization. Every app run should create the visualizations.

## 20. Fix exporter type errors

> Address the type errors reported around line 110 in `export_outputs.py`.

## 21. Label chart points and add normalized prices

> Change the visualizations so every point has a label using `itemNumber` or another identifying attribute.
>
> Add a second line with normalized prices: price per milligram for that item number. For example, 5 mg at 5000 equals 1000 per mg.

## 22. Offset chart labels

> Avoid labels being placed on top of each other by adding vertical offsets.

## 23. Procurement research and enrichment

> Use `https://www.sykehusinnkjop.no` and `https://www.doffin.no` to populate `tenderRef`, `noticeId`, and `title`.

The accompanying research brief required high-precision, evidence-backed enrichment using authoritative Norwegian sources. It required preserving existing values, never inventing procurement data, leaving unverifiable fields NULL, matching by item number where possible, and creating provenance, evidence, source assessment, and schema recommendations. It specifically required investigating the example `Anagrelide Viatris`, item number `107216`, strength `0.5 mg`, pack size `100`.

## 24. Remove hardcoded input molecules

> There can be no hardcoding of any input molecules. The procurement module path was also incorrect and needed to use the existing `python-docker-src/src/modules` path.

## 25. Remove hardcoded procurement source data

> Explain why the procurement source registry and molecule-specific values were hardcoded, and remove that hardcoded material. Procurement values should be discovered from downloaded official source content and matched against the molecules configured in `input_molecules.py`.

## 26. Add yearly consumption charts

> Add another chart for each molecule in `input_molecules.py`, using the `consumptionData` array. Plot yearly consumption values with one point per year and include the listed unit.

## 27. Make output generation automatic

> Add `write_csv` to `main.py`, remove any requirement to manually request CSV or PNG output, and run CSV and PNG generation every time the app runs.

## 28. Make the default Make target shut down after app completion

> Have the `all` target wait for the `app` container to close, then run the `down` target.

## 29. Improve README structure and documentation

> Look at `README.md` and replace the section comments with actual Markdown sections. Fix the `Caching` link so it takes the user to the relevant section. Review Section B for completeness and describe every `.py` file in fewer than 40 words.

## 30. Create this prompt record

> Write `agentprompts.md` and list all prompts related to this entire assignment in `/home/jose/assignmentCGS`.

