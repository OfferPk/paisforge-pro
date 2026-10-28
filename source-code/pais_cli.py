#!/usr/bin/env python3
"""
PAISForge Pro (v1.0.0) - Back-End CLI & SIP Ingest Automation Tool
Standard: CCSDS 651.1-B-1 (Blue Book, February 2014 / ISO 20104:2015)
"""

import argparse
import hashlib
import json
import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

class PAISCLI:
    def __init__(self):
        self.schema_urn = "urn:ccsds:schema:pais:1.0"

    def create_sample_descriptor(self, descriptor_id="DESC-JUICE-JANUS-L2"):
        now = datetime.now(timezone.utc).isoformat()
        return {
            "standard": "CCSDS 651.1-B-1",
            "iso_equivalent": "ISO 20104:2015",
            "paimas_standard": "CCSDS 651.0-M-1 (ISO 20652)",
            "schema_urn": self.schema_urn,
            "descriptor_id": descriptor_id,
            "title": "JUICE JANUS Optical Camera Calibrated Science Product",
            "producer_agency": "ESA-SOC",
            "archive_agency": "ESA-PSA",
            "packaging_binding": "CCSDS_661_0_XFDU",
            "transport_protocol": "HTTPS_TLS13_REST",
            "created_at": now,
            "collection_groups": [
                {
                    "group_id": "COL-SCIENCE-IMG",
                    "title": "Calibrated FITS Science Rasters",
                    "min_occurs": 1,
                    "max_occurs": 100
                },
                {
                    "group_id": "COL-PDS4-META",
                    "title": "PDS4 XML Companion Labels",
                    "min_occurs": 1,
                    "max_occurs": 100
                }
            ],
            "data_object_specs": [
                {
                    "spec_id": "SPEC-FITS-RASTER",
                    "data_type": "ScientificImage",
                    "mime_type": "image/fits",
                    "min_bytes": 1024,
                    "max_bytes": 536870912,
                    "checksum_algo": "SHA-256"
                },
                {
                    "spec_id": "SPEC-PDS4-LABEL",
                    "data_type": "PDS4XMLMetadata",
                    "mime_type": "application/xml",
                    "min_bytes": 256,
                    "max_bytes": 1048576,
                    "checksum_algo": "SHA-256"
                }
            ]
        }

    def create_sample_sip(self, descriptor_id="DESC-JUICE-JANUS-L2"):
        fits_hash = hashlib.sha256(b"JUICE_JANUS_GANYMEDE_ORBIT_012_FITS_PAYLOAD").hexdigest()
        xml_hash = hashlib.sha256(b"JUICE_JANUS_GANYMEDE_ORBIT_012_PDS4_LABEL").hexdigest()
        return {
            "sip_id": "SIP-JUICE-JANUS-20261020-001",
            "descriptor_id": descriptor_id,
            "session_id": "PAIS-SESSION-517",
            "producer_agency": "ESA-SOC",
            "archive_agency": "ESA-PSA",
            "items": [
                {
                    "item_id": "JAN_20261020T120000_GAN_L2.fits",
                    "spec_id": "SPEC-FITS-RASTER",
                    "mime_type": "image/fits",
                    "size_bytes": 33554432,
                    "checksum": fits_hash,
                    "checksum_algo": "SHA-256"
                },
                {
                    "item_id": "JAN_20261020T120000_GAN_L2.xml",
                    "spec_id": "SPEC-PDS4-LABEL",
                    "mime_type": "application/xml",
                    "size_bytes": 12288,
                    "checksum": xml_hash,
                    "checksum_algo": "SHA-256"
                }
            ]
        }

    def validate_ingest(self, descriptor, sip):
        violations = []
        if sip.get("descriptor_id") != descriptor.get("descriptor_id"):
            violations.append("Descriptor ID mismatch")

        specs_by_id = {s["spec_id"]: s for s in descriptor.get("data_object_specs", [])}
        items = sip.get("items", [])

        for spec_id, spec in specs_by_id.items():
            matched = [i for i in items if i.get("spec_id") == spec_id]
            if not matched:
                violations.append(f"Missing required item for spec {spec_id}")
            for m in matched:
                if m.get("mime_type") != spec.get("mime_type"):
                    violations.append(f"MIME mismatch on {m.get('item_id')}")
                if not (spec["min_bytes"] <= m.get("size_bytes", 0) <= spec["max_bytes"]):
                    violations.append(f"Size out of bounds on {m.get('item_id')}")
                if len(m.get("checksum", "")) != 64:
                    violations.append(f"Invalid SHA-256 digest on {m.get('item_id')}")

        total_bytes = sum(i.get("size_bytes", 0) for i in items)
        return {
            "sip_id": sip.get("sip_id"),
            "descriptor_id": descriptor.get("descriptor_id"),
            "session_state": "INGEST_ARCHIVED" if len(violations) == 0 else "REJECTED_ANOMALY",
            "items_validated": len(items),
            "total_ingest_mb": round(total_bytes / (1024 * 1024), 2),
            "violations_count": len(violations),
            "violations": violations,
            "ingest_verdict": "ACCEPTED_ISO_20104" if len(violations) == 0 else "REJECTED"
        }

    def generate_descriptor_xml(self, desc):
        root = ET.Element("pais:transferObjectTypeDescriptor", {
            "xmlns:pais": self.schema_urn,
            "version": "1.0.0"
        })
        ident = ET.SubElement(root, "identification")
        ET.SubElement(ident, "standard").text = desc.get("standard")
        ET.SubElement(ident, "iso_equivalent").text = desc.get("iso_equivalent")
        ET.SubElement(ident, "descriptor_id").text = desc.get("descriptor_id")
        ET.SubElement(ident, "descriptor_title").text = desc.get("title")
        ET.SubElement(ident, "producer_agency").text = desc.get("producer_agency")
        ET.SubElement(ident, "archive_agency").text = desc.get("archive_agency")

        cols = ET.SubElement(root, "collectionGroups", count=str(len(desc.get("collection_groups", []))))
        for c in desc.get("collection_groups", []):
            ET.SubElement(cols, "collectionGroup", {
                "ID": c["group_id"],
                "title": c["title"],
                "minOccurs": str(c["min_occurs"]),
                "maxOccurs": str(c["max_occurs"])
            })

        specs = ET.SubElement(root, "dataObjectSpecifications", count=str(len(desc.get("data_object_specs", []))))
        for s in desc.get("data_object_specs", []):
            sp_el = ET.SubElement(specs, "dataObjectSpec", {
                "ID": s["spec_id"],
                "dataType": s["data_type"],
                "mimeType": s["mime_type"]
            })
            ET.SubElement(sp_el, "sizeBounds", {
                "minBytes": str(s["min_bytes"]),
                "maxBytes": str(s["max_bytes"])
            })
            ET.SubElement(sp_el, "fixityPolicy", {
                "algorithm": s["checksum_algo"],
                "mandatory": "true"
            })

        return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

def main():
    parser = argparse.ArgumentParser(description="PAISForge Pro - CCSDS 651.1-B-1 / ISO 20104 PAIS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    subparsers.add_parser("create-descriptor", help="Generate a negotiated Transfer Object Type Descriptor")
    subparsers.add_parser("create-sip", help="Generate a sample Submission Information Package (SIP)")
    subparsers.add_parser("validate-ingest", help="Validate SIP ingest against negotiated descriptor")
    subparsers.add_parser("export-xml", help="Export canonical CCSDS 651.1-B-1 Descriptor XML")
    subparsers.add_parser("audit", help="Run 10-point normative compliance audit")

    args = parser.parse_args()
    cli = PAISCLI()

    if args.command == "create-descriptor":
        print(json.dumps(cli.create_sample_descriptor(), indent=2))
    elif args.command == "create-sip":
        print(json.dumps(cli.create_sample_sip(), indent=2))
    elif args.command == "validate-ingest":
        desc = cli.create_sample_descriptor()
        sip = cli.create_sample_sip()
        print(json.dumps(cli.validate_ingest(desc, sip), indent=2))
    elif args.command == "export-xml":
        desc = cli.create_sample_descriptor()
        print(cli.generate_descriptor_xml(desc))
    elif args.command == "audit":
        import subprocess
        subprocess.run(["node", "source-code/pais-auditor.js"])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
