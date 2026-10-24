"""A document's time axes as a TimeToShare manifest, the `.tla` file's `timetoshare`.

TimeToShare (https://github.com/TimeToAlign/TimeToShare) describes the
structure of musical timelines, their units, lengths and how they relate,
without their events. A `.tla` file's components are events; the axes they lie
on are the media's and the scores'. Written as a manifest, any program that
reads TimeToShare knows them without knowing TiLiA. The schema's
`timetoshare` says which root timelines the manifest has; this builds them.
"""

from __future__ import annotations

import math
from typing import Any

from tilia_core.tla.model import Document

TIMETOSHARE_VERSION = "0.1.0"
MEDIA_TIMELINE = "media"
# The quarters axis of a file whose time_unit is quarters but that has no score.
SCORE_TIMELINE = "score"


def manifest(document: Document) -> dict[str, Any]:
    """The document's axes as a TimeToShare manifest, in its minimal form.

    Its id is the document's. It has the root `media`, in seconds, when the
    document has media or its time_unit is seconds, and one root in quarters
    for each score, in id order, its id the score's; `score` stands in for a
    quarters document without one. A length the document doesn't know is
    null, as every score's is: the core doesn't compute a score's length.
    """
    timelines: list[dict[str, Any]] = []
    if document.media_path or document.time_unit == "seconds":
        timelines.append(_media(document))
    timelines.extend(_score(score_id) for score_id in sorted(document.scores))
    if document.time_unit == "quarters" and not document.scores:
        timelines.append(_score(SCORE_TIMELINE))
    return {
        "timetoshare": TIMETOSHARE_VERSION,
        "id": document.document_id,
        "timelines": timelines,
    }


def time_axis(document: Document) -> str | None:
    """The id of the manifest's root that the document's times lie on, or
    None for a quarters document with several scores, which the format
    doesn't place on one of them."""
    if document.time_unit == "seconds":
        return MEDIA_TIMELINE
    if not document.scores:
        return SCORE_TIMELINE
    if len(document.scores) == 1:
        return next(iter(document.scores))
    return None


def _media(document: Document) -> dict[str, Any]:
    timeline: dict[str, Any] = {
        "id": MEDIA_TIMELINE,
        "unit": "seconds",
        "length": _seconds(document.media_length),
    }
    if document.media_path:
        timeline["name"] = document.media_path.rsplit("/", 1)[-1]
    return timeline


def _score(timeline_id: str) -> dict[str, Any]:
    return {"id": timeline_id, "unit": "quarters", "length": None}


def _seconds(length: Any) -> float | None:
    """A media length as TimeToShare writes it on a float axis, or None for
    one the format doesn't allow, which the core reads as no length."""
    if isinstance(length, bool) or not isinstance(length, (int, float)):
        return None
    try:
        seconds = float(length)
    except OverflowError:  # an integer too large for a float
        return None
    return seconds if math.isfinite(seconds) and seconds > 0 else None
