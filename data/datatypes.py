from __future__ import annotations
 
from dataclasses import dataclass
from datetime import datetime

#SourceFile data class for the files we recieve from drives
@dataclass(frozen=True)
class SourceFile:
    account_id: str
    source: str
    external_id: str
    name: str
    path: str
    mime_type: str
    source_hash: str | None
    modified_time: datetime
    size_bytes: int | None