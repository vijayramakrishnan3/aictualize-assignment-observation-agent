"""Identical bodies more than a day apart are separate instances, not duplicates."""

from pipeline.parse import Parsed, mark_duplicates


def _msg(path: str, date: str | None) -> Parsed:
    return Parsed(
        id=path.replace("/", "-"),
        path=path,
        mailbox="m",
        folder="f",
        header_message_id=None,
        date_iso=date,
        date_source="header" if date else None,
        from_addr="a@x.com",
        to_addrs=[],
        cc_addrs=[],
        subject="Daily Nomination",
        subject_norm="daily nomination",
        body_raw="See attached.",
        body_clean="See attached.",
        thread_key="t",
    )


def test_daily_sends_with_identical_bodies_are_not_duplicates():
    msgs = [
        _msg("m/f/1.", "2000-07-27T07:26:00Z"),
        _msg("m/f/2.", "2000-07-31T07:20:00Z"),
        _msg("m/f/3.", "2000-08-02T07:19:00Z"),
    ]
    assert mark_duplicates(msgs) == 0
    assert all(m.dup_of is None for m in msgs)


def test_same_body_within_a_day_is_a_duplicate():
    msgs = [
        _msg("m/f/1.", "2001-03-05T10:00:00Z"),
        _msg("m/f/2.", "2001-03-05T16:00:00Z"),
    ]
    assert mark_duplicates(msgs) == 1
    assert msgs[1].dup_of == msgs[0].id


def test_undated_copy_joins_the_cluster():
    msgs = [_msg("m/f/1.", "2001-03-05T10:00:00Z"), _msg("m/f/2.", None)]
    assert mark_duplicates(msgs) == 1
