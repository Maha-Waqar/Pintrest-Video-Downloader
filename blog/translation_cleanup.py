"""Utilities for cleaning translated HTML content and rewriting internal links."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup, NavigableString, Tag


def _allowed_tags_from_original(html: str) -> Set[str]:
    """Return the set of tag names present in the original HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    return {tag.name for tag in soup.find_all(True)}


def _normalize_lists(original_soup: BeautifulSoup, translated_soup: BeautifulSoup) -> None:
    """Align unordered and ordered lists with the original structure."""
    original_lists = original_soup.find_all(["ul", "ol"])
    translated_lists = translated_soup.find_all(["ul", "ol"])

    # Remove extra lists that do not exist in the source content
    if len(translated_lists) > len(original_lists):
        for extra in translated_lists[len(original_lists) :]:
            extra.decompose()
        translated_lists = translated_soup.find_all(["ul", "ol"])

    for index, translated_list in enumerate(translated_lists):
        original_list: Optional[Tag] = original_lists[index] if index < len(original_lists) else None
        if original_list is None:
            translated_list.decompose()
            continue

        # Force list type (ordered/unordered) to match source
        if translated_list.name != original_list.name:
            translated_list.name = original_list.name

        # Copy basic structural attributes from the source list
        for attr in ("type", "start", "reversed", "class", "style"):
            if attr in original_list.attrs:
                translated_list[attr] = original_list[attr]
            elif attr in translated_list.attrs:
                del translated_list[attr]

        desired_count = len(original_list.find_all("li", recursive=False))

        # Remove nested <li> wrappers or empty list entries
        items = translated_list.find_all("li", recursive=False)
        for item in list(items):
            # Promote nested list items if the translator embedded them
            nested_items = item.find_all("li")
            if nested_items:
                for nested in nested_items:
                    translated_list.insert(translated_list.contents.index(item), nested)
                item.decompose()
                continue

            # Drop empty items introduced by the translator
            if not item.get_text(strip=True):
                item.decompose()

        items = translated_list.find_all("li", recursive=False)
        if desired_count and len(items) > desired_count:
            for extra in items[desired_count:]:
                extra.decompose()
            items = translated_list.find_all("li", recursive=False)

        # Ensure every list item wraps its textual content in <p> if that
        # matches the source structure (helps keep formatting consistent)
        original_items = original_list.find_all("li", recursive=False)
        for idx, li in enumerate(items):
            source_item = original_items[idx] if idx < len(original_items) else None
            if source_item is None:
                continue

            for attr in ("class", "style"):
                if attr in source_item.attrs:
                    li[attr] = source_item[attr]
                elif attr in li.attrs:
                    del li[attr]

            needs_paragraph = any(
                child.name == "p" for child in source_item.children if isinstance(child, Tag)
            )
            if needs_paragraph and not any(child.name == "p" for child in li.children if isinstance(child, Tag)):
                content = list(li.contents)
                li.clear()
                paragraph = translated_soup.new_tag("p")
                for child in content:
                    paragraph.append(child)
                li.append(paragraph)


def _remove_disallowed_tags(translated_soup: BeautifulSoup, allowed_tags: Set[str]) -> None:
    """Remove wrapper tags that are not present in the original structure."""
    for tag in translated_soup.find_all(True):
        if tag.name in {"html", "body"}:
            continue
        if tag.name not in allowed_tags:
            tag.unwrap()


def _strip_redundant_breaks(translated_soup: BeautifulSoup, allowed_tags: Set[str]) -> None:
    """Remove <br> tags when the original content does not include them."""
    if "br" in allowed_tags:
        return
    for br in translated_soup.find_all("br"):
        br.decompose()


def _structure_is_fragmented(original_soup: BeautifulSoup, translated_soup: BeautifulSoup) -> bool:
    """
    Return True when the translated markup lost too much of the original structure.

    We compare total tag counts and a subset of critical tags (headings, lists, and
    paragraphs). If the translated HTML is mostly plain text or strips these tags,
    we rebuild it from the source skeleton so spacing and hierarchy stay intact.
    """
    original_tags = original_soup.find_all(True)
    translated_tags = translated_soup.find_all(True)

    if not original_tags:
        return False
    if not translated_tags:
        return True

    original_count = len(original_tags)
    translated_count = len(translated_tags)
    if translated_count / original_count < 0.5:
        return True

    critical = {"p", "ol", "ul", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
    original_critical = sum(1 for tag in original_tags if tag.name in critical)
    translated_critical = sum(1 for tag in translated_tags if tag.name in critical)
    if original_critical and (translated_critical / original_critical) < 0.6:
        return True

    return False


def _restore_structure_from_original(
    original_soup: BeautifulSoup, translated_soup: BeautifulSoup
) -> BeautifulSoup:
    """
    Clone the original HTML skeleton and populate its text nodes with translated copy.

    This fallback keeps the same tag hierarchy as the source while still using the
    translated strings we received (in order) so the rendered page layout matches.
    """
    def _extract_translation_segments() -> List[str]:
        segments = [string.strip() for string in translated_soup.stripped_strings if string.strip()]
        if len(segments) <= 1:
            raw_text = translated_soup.get_text("\n", strip=True)
            parts = re.split(r"\n{2,}|\n(?=\d+\.\s)", raw_text)
            segments = [part.strip() for part in parts if part and part.strip()]
            line_split = [line.strip() for line in raw_text.splitlines() if line.strip()]
            if len(line_split) > len(segments):
                segments = line_split
        if len(segments) <= 1:
            raw_text = translated_soup.get_text(" ", strip=True)
            parts = re.split(r"(?<=[.!?])\s+", raw_text)
            segments = [part.strip() for part in parts if part.strip()]
        return segments

    def _fill_target_with_segment(target: Tag, segment: str) -> None:
        link_children = [
            child for child in target.contents if isinstance(child, Tag) and child.name == "a"
        ]

        if len(link_children) == 1 and all(
            isinstance(child, (Tag, NavigableString)) and (
                (isinstance(child, NavigableString) and not child.strip()) or child == link_children[0]
            )
            for child in target.contents
        ):
            anchor = link_children[0]
            target.clear()
            target.append(anchor)
            anchor.clear()
            anchor.append(segment)
            return

        target.clear()
        target.append(segment)

    translated_segments = _extract_translation_segments()
    if not translated_segments:
        return BeautifulSoup(str(original_soup), "html.parser")

    rebuilt = BeautifulSoup(str(original_soup), "html.parser")
    targets = rebuilt.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"])

    for idx, target in enumerate(targets):
        fallback = target.get_text(" ", strip=True)
        if idx < len(translated_segments):
            segment = translated_segments[idx]
        else:
            segment = fallback or (translated_segments[-1] if translated_segments else "")
        _fill_target_with_segment(target, segment)

    return rebuilt


def _rewrite_internal_hrefs(translated_soup: BeautifulSoup, slug_lookup: Dict[str, str]) -> None:
    """Update anchor href attributes so they use localized slugs."""
    if not slug_lookup:
        return

    for anchor in translated_soup.find_all("a"):
        href = anchor.get("href")
        if not href:
            continue

        parsed = urlparse(href)
        if not parsed.path:
            continue

        # Break path into segments, ignoring leading/trailing slashes
        raw_segments = parsed.path.split("/")
        segments: List[str] = [segment for segment in raw_segments if segment]
        if not segments:
            continue

        updated = False
        for idx, segment in enumerate(segments):
            translated_slug = slug_lookup.get(segment)
            if translated_slug:
                segments[idx] = translated_slug
                updated = True
                break

        if not updated:
            continue

        # Re-assemble the path, preserving a trailing slash if present originally
        trimmed_path = "/".join(segments)
        new_path = f"/{trimmed_path}"
        if parsed.path.endswith("/"):
            new_path = f"{new_path}/"

        rewritten = parsed._replace(path=new_path)
        anchor["href"] = urlunparse(rewritten)


def _soup_to_markup(soup: BeautifulSoup) -> str:
    """Convert the soup back to a markup string without enclosing <html> tags."""
    if soup.body:
        return "".join(str(child) for child in soup.body.children)
    return soup.decode()


def clean_translation_html(
    original_html: str,
    translated_html: str,
    slug_lookup: Dict[str, str],
) -> str:
    """Return a cleaned translation that mirrors the source structure."""
    allowed_tags = _allowed_tags_from_original(original_html)

    original_soup = BeautifulSoup(original_html or "", "html.parser")
    translated_soup = BeautifulSoup(translated_html or "", "html.parser")

    _remove_disallowed_tags(translated_soup, allowed_tags)
    _strip_redundant_breaks(translated_soup, allowed_tags)
    _normalize_lists(original_soup, translated_soup)
    if _structure_is_fragmented(original_soup, translated_soup):
        translated_soup = _restore_structure_from_original(original_soup, translated_soup)
    _rewrite_internal_hrefs(translated_soup, slug_lookup)

    # Trim leading/trailing whitespace-only nodes at the top level
    for element in list(translated_soup.contents):
        if isinstance(element, NavigableString) and not element.strip():
            element.extract()

    cleaned = _soup_to_markup(translated_soup)
    return cleaned.strip()


def build_slug_lookup(posts: Iterable[object], language: str) -> Dict[str, str]:
    """Return a mapping of default-language slugs to localized slugs for the given language."""
    lookup: Dict[str, str] = {}
    for post in posts:
        base_slug = getattr(post, "slug", None)
        if not base_slug:
            continue
        translated_slug = getattr(post, "get_translated_slug", lambda **_: base_slug)(language=language)
        lookup[str(base_slug)] = str(translated_slug or base_slug)
    return lookup
