from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


RESOURCE_PATTERNS: Dict[str, re.Pattern[str]] = {
    "ROB": re.compile(r"rob.*(head|tail|busy)", re.IGNORECASE),
    "IssueQueue": re.compile(r"issue.*(valid|alloc|ready|slot)", re.IGNORECASE),
    "LSQ": re.compile(r"(ldq|stq|loadqueue|storequeue)", re.IGNORECASE),
    "MSHR_LFB": re.compile(r"(mshr|linebuffer|lfb)", re.IGNORECASE),
    "WriteBuffer": re.compile(r"(writebuffer|storebuffer)", re.IGNORECASE),
    "BTB": re.compile(r"btb", re.IGNORECASE),
    "RSB": re.compile(r"(rsb|returnstack)", re.IGNORECASE),
}


@dataclass
class ScanHit:
    resource: str
    file: str
    line: int
    snippet: str

    def to_dict(self) -> Dict[str, str | int]:
        return {
            "resource": self.resource,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
        }


def scan_rtl(directory: Path, extensions: Iterable[str]) -> List[ScanHit]:
    hits: List[ScanHit] = []
    for path in _iter_files(directory, extensions):
        hits.extend(_scan_file(path))
    return hits


def write_scan_report(hits: List[ScanHit], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"matches": [hit.to_dict() for hit in hits]}
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)


def _iter_files(directory: Path, extensions: Iterable[str]) -> Iterable[Path]:
    normalized = {ext.lower().lstrip(".") for ext in extensions}
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower().lstrip(".") in normalized:
            yield path


def _scan_file(path: Path) -> List[ScanHit]:
    hits: List[ScanHit] = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            for resource, pattern in RESOURCE_PATTERNS.items():
                if pattern.search(line):
                    hits.append(
                        ScanHit(
                            resource=resource,
                            file=str(path),
                            line=line_no,
                            snippet=line.strip(),
                        )
                    )
    return hits
