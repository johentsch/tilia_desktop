import json

import pytest

from tilia_core.tla import Document, Score, canonical_bytes, loads, new_document
from tilia_core.tla.timetoshare import MEDIA_TIMELINE, manifest, time_axis

SCORE = "01900000-0000-7000-8000-000000000001"
OTHER_SCORE = "01900000-0000-7000-8000-000000000002"


def _with_score(document, score_id):
    document.scores[score_id] = Score(id=score_id, format="mei", source={})
    return document


def _written(document):
    return json.loads(canonical_bytes(document))


def test_a_new_document_has_the_media_axis_of_unknown_length():
    doc = new_document()
    assert doc.timetoshare == {
        "id": doc.document_id,
        "timelines": [{"id": "media", "length": None, "unit": "seconds"}],
        "timetoshare": "0.1.0",
    }
    assert doc.media_length is None
    assert time_axis(doc) == MEDIA_TIMELINE


def test_the_media_length_is_kept_in_the_manifest_only():
    doc = new_document()
    doc.media_path = "recordings/take 1.mp3"
    doc.media_length = 183.5
    written = _written(doc)
    assert written["media"] == {"path": "recordings/take 1.mp3"}
    assert written["timetoshare"]["timelines"] == [
        {"id": "media", "length": 183.5, "unit": "seconds"}
    ]
    assert loads(canonical_bytes(doc)).media_length == 183.5


def test_the_media_length_is_read_from_the_manifest():
    doc = new_document()
    content = _written(doc)
    content["timetoshare"]["timelines"][0]["length"] = 61.25
    assert loads(json.dumps(content).encode()).media_length == 61.25


def test_setting_a_length_adds_the_media_axis_where_it_is_missing():
    doc = Document(document_id=SCORE, format_version="1.0.0-draft.1")
    assert doc.media_length is None
    doc.media_length = 2.0
    assert doc.timetoshare == {
        "timetoshare": "0.1.0",
        "timelines": [{"id": "media", "unit": "seconds", "length": 2.0}],
    }


def test_a_manifest_without_the_media_axis_has_no_length():
    doc = new_document()
    doc.timetoshare = {"timetoshare": "0.1.0", "timelines": "not a list"}
    assert doc.media_length is None


def test_media_and_scores_each_have_an_axis():
    doc = new_document()
    doc.media_path = "a.ogg"
    _with_score(_with_score(doc, OTHER_SCORE), SCORE)
    timelines = manifest(doc)["timelines"]
    assert [t["id"] for t in timelines] == [MEDIA_TIMELINE, SCORE, OTHER_SCORE]
    assert [t["unit"] for t in timelines] == ["seconds", "quarters", "quarters"]


def test_a_quarters_file_lies_on_its_score():
    doc = _with_score(new_document(time_unit="quarters"), SCORE)
    assert manifest(doc)["timelines"] == [
        {"id": SCORE, "length": None, "unit": "quarters"}
    ]
    assert time_axis(doc) == SCORE


@pytest.mark.parametrize("scores", [[], [SCORE, OTHER_SCORE]])
def test_a_quarters_file_without_one_score_has_no_axis(scores):
    doc = new_document(time_unit="quarters")
    for score_id in scores:
        _with_score(doc, score_id)
    assert time_axis(doc) is None
    assert [t["id"] for t in manifest(doc)["timelines"]] == scores


def test_what_the_manifest_holds_is_kept():
    doc = new_document()
    doc.media_length = 60.0
    # What another program added: a second recording, aligned with the media.
    doc.timetoshare["timelines"].append(
        {"id": "take 2", "unit": "seconds", "length": 61.25}
    )
    doc.timetoshare["groups"] = [{"id": "takes", "members": ["media", "take 2"]}]
    written = canonical_bytes(doc)
    again = loads(written)
    assert again.timetoshare["groups"] == [
        {"id": "takes", "members": ["media", "take 2"]}
    ]
    assert again.timetoshare["timelines"][1] == {
        "id": "take 2",
        "length": 61.25,
        "unit": "seconds",
    }
    assert canonical_bytes(again) == written


def test_the_manifest_is_written_in_one_key_order():
    doc = new_document()
    doc.timetoshare = {
        "timetoshare": "0.1.0",
        "timelines": [{"unit": "seconds", "length": 1.0, "id": "media"}],
        "id": doc.document_id,
    }
    timetoshare = _written(doc)["timetoshare"]
    assert list(timetoshare) == ["id", "timelines", "timetoshare"]
    assert list(timetoshare["timelines"][0]) == ["id", "length", "unit"]


def test_the_manifest_is_valid_timetoshare():
    timetoshare = pytest.importorskip("timetoshare")
    doc = new_document()
    doc.media_path = "a.wav"
    doc.media_length = 3.25
    _with_score(doc, SCORE)
    timetoshare.validate(manifest(doc))
    timetoshare.validate(manifest(new_document(time_unit="quarters")))
