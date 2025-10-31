from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

@dataclass
class Book:
    id: str
    title: str
    author: str
    year: Optional[int] = None
    genre: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    isbn: Optional[str] = None
    pages: Optional[int] = None
    quotes: List[str] = field(default_factory=list)
    added_at: str = field(default_factory=_now_iso)

    @staticmethod
    def create(
        title: str,
        author: str,
        year: Optional[int] = None,
        genre: Optional[str] = None,
        tags: Optional[List[str]] = None,
        isbn: Optional[str] = None,
        pages: Optional[int] = None,
    ) -> "Book":
        return Book(
            id=str(uuid.uuid4()),
            title=title.strip(),
            author=author.strip(),
            year=int(year) if year is not None else None,
            genre=genre.strip() if genre else None,
            tags=[t.strip() for t in (tags or []) if t.strip()],
            isbn=isbn.strip() if isbn else None,
            pages=int(pages) if pages is not None else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Book":
        return Book(
            id=str(data.get("id") or uuid.uuid4()),
            title=data["title"],
            author=data["author"],
            year=int(data["year"]) if data.get("year") not in (None, "") else None,
            genre=data.get("genre"),
            tags=list(data.get("tags", [])),
            isbn=data.get("isbn"),
            pages=int(data["pages"]) if data.get("pages") not in (None, "") else None,
            quotes=list(data.get("quotes", [])),
            added_at=data.get("added_at") or _now_iso(),
        )
