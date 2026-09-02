A table on mongodb will have these columns, write a python type/class as the source of truth to be used when making that table.

Table A:
noticeId - Notice Identifier
tenderRef - Tender code or internal reference
title - Tender or notice title
country - NO
buyer - Contracting authority
productMolecule - Target molecule, normalised to the English name
moleculeDetected - Whether the molecule was explicitly found
moleculeVariant - Exact matched term as it appeared
detectionMethod - How you matched it (e.g. name indocument, codein title)
atcCode - ATC code where available
itemNumber - Norwegian item number
productName - Brand or product name as listed
strength - e.g. 5mg
packSize - e.g. 56
supplier - Supplier or MA holder
maxPrice - Regulated maximum price
packSoldLast12m - Historical volume 
estimatedValue - Awarded value, if published
currency - NOK
noticeType - Type of notice
status - Notice status
publicationDate - YYYY-MM-DD ISO
contractStart - YYYY-MM-DD iso
procedureType - Procurement procedure
sourceDocument - Filename or document title
sourceUrl - Notice or document URL

Table B:
To be used in the first stage of browsing/finding via wikipedia:
atcCodes atcCode[] // atcCode consists of the atcCode, and the start/end period for which it is applicable
productMolecule
