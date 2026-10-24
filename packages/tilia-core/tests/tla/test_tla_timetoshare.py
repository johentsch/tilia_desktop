import json

import pytest

from tilia_core.tla import Score, canonical_bytes, loads, new_document
from tilia_core.tla.timetoshare import (
    MEDIA_TIMELINE,
    SCORE_TIMELINE,
    manifest,
    time_axis,
)


def _with_score(document, score_id):
    document.scores[score_id] = Score(id=score_id, format="mei", source={})
    return document


def test_a_seconds_file_has_the_media_axis():
    doc = new_document()
    doc.media_path = "recordings/take 1.mp3"
    doc.media_length = 183
    assert manifest(doc) == {
        "timetoshare": "0.1.0",
        "id": doc.document_id,
        "timelines": [
            {"id": "media", "unit": "seconds", "length": 183.0, "name": "take 1.mp3"}
        ],
    }
    assert time_axis(doc) == MEDIA_TIMELINE


def test_a_seconds_file_without_media_has_a_media_axis_of_unknown_length():
    doc = new_document()
    assert manifest(doc)["timelines"] == [
        {"id": "media", "unit": "seconds", "length": None}
    ]


@pytest.mark.parametrize("length", [0, -1.5, True, 10**400, "12"])
def test_a_media_length_the_format_does_not_allow_is_unknown(length):
    doc = new_document()
    doc.media_length = length
    assert manifest(doc)["timelines"][0]["length"] is None


def test_media_and_scores_each_have_an_axis():
    doc = new_document()
    doc.media_path = "a.ogg"
    doc.media_length = 10.5
    second, first = (
        "01900000-0000-7000-8000-000000000002",
        "01900000-0000-7000-8000-000000000001",
    )
    _with_score(_with_score(doc, second), first)
    timelines = manifest(doc)["timelines"]
    assert [t["id"] for t in timelines] == [MEDIA_TIMELINE, first, second]
    assert [t["unit"] for t in timelines] == ["seconds", "quarters", "quarters"]


def test_a_quarters_file_lies_on_its_score():
    doc = _with_score(
        new_document(time_unit="quarters"), "01900000-0000-7000-8000-000000000001"
    )
    assert manifest(doc)["timelines"] == [
        {
            "id": "01900000-0000-7000-8000-000000000001",
            "unit": "quarters",
            "length": None,
        }
    ]
    assert time_axis(doc) == "01900000-0000-7000-8000-000000000001"


def test_a_quarters_file_without_a_score_has_a_score_axis():
    doc = new_document(time_unit="quarters")
    assert [t["id"] for t in manifest(doc)["timelines"]] == [SCORE_TIMELINE]
    assert time_axis(doc) == SCORE_TIMELINE


def test_a_quarters_file_with_several_scores_has_no_one_axis():
    doc = new_document(time_unit="quarters")
    _with_score(doc, "01900000-0000-7000-8000-000000000001")
    _with_score(doc, "01900000-0000-7000-8000-000000000002")
    assert time_axis(doc) is None


def test_the_manifest_is_kept_as_written():
    doc = new_document()
    doc.media_length = 60.0
    held = manifest(doc)
    # What another program added: a second recording, aligned with the media.
    held["timelines"].append({"id": "take 2", "unit": "seconds", "length": 61.25})
    held["groups"] = [{"id": "takes", "members": ["media", "take 2"]}]
    doc.timetoshare = held
    written = canonical_bytes(doc)
    again = loads(written)
    assert again.timetoshare == held
    assert canonical_bytes(again) == written
    assert json.loads(written)["timetoshare"] == held


def test_a_file_without_a_manifest_has_none():
    doc = new_document()
    written = canonical_bytes(doc)
    assert "timetoshare" not in json.loads(written)
    assert loads(written).timetoshare is None


def test_the_manifest_is_valid_timetoshare():
    timetoshare = pytest.importorskip("timetoshare")
    doc = new_document()
    doc.media_path = "a.wav"
    doc.media_length = 3.25
    _with_score(doc, "01900000-0000-7000-8000-000000000001")
    timetoshare.validate(manifest(doc))
    timetoshare.validate(manifest(new_document(time_unit="quarters")))
