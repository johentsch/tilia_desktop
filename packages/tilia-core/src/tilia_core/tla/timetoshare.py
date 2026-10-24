"""A document's time axes as a TimeToShare manifest, the `.tla` file's `timetoshare`.

TimeToShare (https://github.com/TimeToAlign/TimeToShare) describes the
structure of musical timelines, their units, lengths and how they relate,
without their events. A `.tla` file's components are events; the axes they lie
on are the media's and the scores'. Written as a manifest, any program that
reads TimeToShare knows them without knowing TiLiA. The manifest is the one
place a file keeps their lengths: the media's length is its `media` timeline's.
The schema's `timetoshare` says which root timelines the manifest has.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tilia_core.tla.model import Document

TIMETOSHARE_VERSION = "0.1.0"
MEDIA_TIMELINE = "media"


def manifest(document: Document) -> dict[str, Any]:
    """The document's manifest as it is written: a copy of the one it holds,
    with the roots the document's axes need added where they are missing.

    Its id is the document's, unless it has one. It has the root `media`, in
    seconds, when the document has media or its time_unit is seconds, and one
    root in quarters for each score, its id the score's. A root that is added has an unknown
    length: a score's always does, as the core doesn't compute one. Nothing
    the manifest holds is changed or taken out, but every object's keys are
    in code-point order, as TimeToShare's writers write them, so that the
    manifest has one form whatever the order it was read in.
    """
    held = copy.deepcopy(document.timetoshare)
    written: dict[str, Any] = {"timetoshare": TIMETOSHARE_VERSION}
    written.update(held)
    written.setdefault("id", document.document_id)
    timelines = written.get("timelines")
    if not isinstance(timelines, list):
        timelines = written["timelines"] = []
    has_media = bool(document.media_path) or document.time_unit == "seconds"
    if has_media and _root(timelines, MEDIA_TIMELINE) is None:
        timelines.insert(0, _media(None))
    for score_id in sorted(document.scores):
        if _root(timelines, score_id) is None:
            timelines.append(_score(score_id))
    return _in_key_order(written)


def media_length(held: dict[str, Any]) -> Any:
    """The length of a manifest's `media` timeline, as it is stored; None
    without one."""
    timeline = _root(held.get("timelines"), MEDIA_TIMELINE)
    return None if timeline is None else timeline.get("length")


def set_media_length(held: dict[str, Any], length: Any) -> None:
    """Make `length` the length of a manifest's `media` timeline, adding the
    timeline, and the manifest's version and timelines, when it has none."""
    held.setdefault("timetoshare", TIMETOSHARE_VERSION)
    timelines = held.get("timelines")
    if not isinstance(timelines, list):
        timelines = held["timelines"] = []
    timeline = _root(timelines, MEDIA_TIMELINE)
    if timeline is None:
        timelines.insert(0, _media(length))
    else:
        timeline["length"] = length


def time_axis(document: Document) -> str | None:
    """The id of the manifest's root that the document's times lie on, or
    None for a quarters document without one score, which the format
    doesn't place on a root."""
    if document.time_unit == "seconds":
        return MEDIA_TIMELINE
    if len(document.scores) == 1:
        return next(iter(document.scores))
    return None


def _in_key_order(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _in_key_order(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_in_key_order(item) for item in value]
    return value


def _root(timelines: Any, timeline_id: str) -> dict[str, Any] | None:
    """The root timeline with this id, None without one; a manifest the
    format doesn't allow, as a reader may hold, has none."""
    if not isinstance(timelines, list):
        return None
    for timeline in timelines:
        if isinstance(timeline, dict) and timeline.get("id") == timeline_id:
            return timeline
    return None


def _media(length: Any) -> dict[str, Any]:
    return {"id": MEDIA_TIMELINE, "unit": "seconds", "length": length}


def _score(timeline_id: str) -> dict[str, Any]:
    return {"id": timeline_id, "unit": "quarters", "length": None}
