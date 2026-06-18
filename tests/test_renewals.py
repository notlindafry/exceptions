"""Persistence view: the 'temporary forever' flag logic and flagged count."""

from __future__ import annotations

from conftest import make_corpus, make_exc

from risk_ledger.engine import Engine
from risk_ledger.validation import validate_corpus
from risk_ledger.views.renewals import flagged_renewals, render_renewals


def _ids(corpus, config):
    return [e.id for e in flagged_renewals(corpus, config)]


def test_flag_logic(config):
    # >= alert_count (3) AND justification never revisited AND active.
    forever = make_exc(eid="FOREVER", renewals={"count": 5, "justification_changed_last": None})
    reexamined = make_exc(eid="REEXAMINED", renewals={"count": 4, "justification_changed_last": "2026-05-01"})
    below = make_exc(eid="BELOW", renewals={"count": 2, "justification_changed_last": None})
    lapsed = make_exc(eid="LAPSED", status="lapsed", renewals={"count": 9, "justification_changed_last": None})
    corpus = make_corpus(exceptions=[forever, reexamined, below, lapsed])
    assert _ids(corpus, config) == ["FOREVER"]


def test_flagged_count_and_descending_sort(config):
    excs = [
        make_exc(eid="A3", renewals={"count": 3, "justification_changed_last": None}),
        make_exc(eid="B7", renewals={"count": 7, "justification_changed_last": None}),
        make_exc(eid="C5", renewals={"count": 5, "justification_changed_last": None}),
        make_exc(eid="D0", renewals={"count": 0, "justification_changed_last": None}),
    ]
    flagged = flagged_renewals(make_corpus(exceptions=excs), config)
    assert len(flagged) == 3
    assert [e.id for e in flagged] == ["B7", "C5", "A3"]


def test_threshold_is_configurable(config):
    e3 = make_exc(eid="E3", renewals={"count": 3, "justification_changed_last": None})
    corpus = make_corpus(exceptions=[e3])
    assert len(flagged_renewals(corpus, config)) == 1   # default alert_count is 3
    config.renewal_alert_count = 4
    assert len(flagged_renewals(corpus, config)) == 0   # now below threshold


def test_render_smoke(config):
    exc = make_exc(eid="EXC-F", renewals={"count": 4, "justification_changed_last": None},
                   with_exception_90ci=[0.05, 0.12])
    corpus = make_corpus(exceptions=[exc])
    validate_corpus(corpus, config)
    eng = Engine(corpus, config)
    text = render_renewals(eng, corpus, config)
    assert "## Persistence" in text
    assert "EXC-F" in text
    assert "| Exception | What was accepted | Renewals | Mapped risk | Owner |" in text
