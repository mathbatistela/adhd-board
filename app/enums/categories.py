"""Category metadata (labels, emojis, inline SVGs)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMetadata:
    """Display metadata for a note category."""

    emoji: str
    label: str
    svg: str


DEFAULT_CATEGORY = CategoryMetadata(
    emoji="⭐",
    label="Nota",
    svg="""
<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <polygon points="24,6 29,19 43,19 32,27 36,40 24,32 12,40 16,27 5,19 19,19"
    fill="none" stroke="#141414" stroke-width="3" stroke-linejoin="round"/>
</svg>
""".strip(),
)


CATEGORY_METADATA: dict[str, CategoryMetadata] = {
    "casa": CategoryMetadata(
        emoji="🏠",
        label="Casa",
        svg="""
<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M8 22 L24 8 L40 22" fill="none" stroke="#141414" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M14 22 V38 H34 V22" fill="none" stroke="#141414" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="20" y="28" width="8" height="10" fill="none" stroke="#141414" stroke-width="3" stroke-linejoin="round"/>
</svg>
""".strip(),
    ),
    "trabalho": CategoryMetadata(
        emoji="💼",
        label="Trabalho",
        svg="""
<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <rect x="8" y="16" width="32" height="22" rx="3" fill="none" stroke="#141414" stroke-width="3"/>
  <path d="M18 16 V12 C18 10.895 18.895 10 20 10 H28 C29.105 10 30 10.895 30 12 V16" fill="none" stroke="#141414" stroke-width="3"/>
  <path d="M8 24 H40" stroke="#141414" stroke-width="3"/>
</svg>
""".strip(),
    ),
    "estudos": CategoryMetadata(
        emoji="📚",
        label="Estudos",
        svg="""
<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M8 16 L24 8 L40 16 V36 L24 44 L8 36 V16" fill="none" stroke="#141414" stroke-width="3" stroke-linejoin="round"/>
  <path d="M24 8 V44" stroke="#141414" stroke-width="3" stroke-linecap="round"/>
</svg>
""".strip(),
    ),
    "saude": CategoryMetadata(
        emoji="💊",
        label="Saúde",
        svg="""
<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <rect x="10" y="14" width="28" height="20" rx="10" fill="none" stroke="#141414" stroke-width="3"/>
  <path d="M19 24 H29" stroke="#141414" stroke-width="3" stroke-linecap="round"/>
  <path d="M24 19 V29" stroke="#141414" stroke-width="3" stroke-linecap="round"/>
</svg>
""".strip(),
    ),
}


def get_category_metadata(category: str) -> CategoryMetadata:
    """Return metadata for category (case-insensitive)."""
    normalized = category.strip().lower()
    if not normalized:
        return DEFAULT_CATEGORY
    return CATEGORY_METADATA.get(normalized, DEFAULT_CATEGORY)
