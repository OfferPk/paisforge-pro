# CCSDS 651.1-B-1 & ISO 20104 Producer-Archive Interface Specification (PAIS)

**Document**: CCSDS 651.1-B-1 (Blue Book, Issue 1, February 2014 / ISO 20104:2015)  
**Companion Methodology**: CCSDS 651.0-M-1 (PAIMAS / ISO 20652\) & CCSDS 650.0-M-3 (OAIS / ISO 14721\)  
**System**: PAISForge Pro (v1.0.0)

## 1\. Executive Summary & Architectural Scope

CCSDS 651.1-B-1 (ratified as ISO 20104:2015) specifies the abstract syntax and XML implementation for describing digital space science and Earth Observation data objects to be transferred from an information Producer (e.g. a spacecraft instrument Science Operations Center) to an Archive (e.g. NASA PDS, ESA PSA, JAXA DARTS).

## 2\. Core Descriptor Specifications

- Transfer Object Type Descriptor () (§3.2): Identification, Collection Groups, and Data Object Specifications.  
- Submission Session & Ingest Validation (§4.1 – §4.4): Structural completeness, MIME & byte bounds, mandatory SHA-256 fixity, and anomaly quarantine.