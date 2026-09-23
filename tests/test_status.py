"""Re-running does not repeat finished model work. No model calls."""

import json

from pipeline import status


def _setup(tmp_path):
    data = tmp_path / "data"
    (data / "validated").mkdir(parents=True)
    (data / "validated" / "batch_001.json").write_text('{"observations": []}')
    (data / "synthesis.json").write_text('{"processes": [], "opportunities": []}')
    return data


def test_synthesis_pending_until_stamped(tmp_path):
    data = _setup(tmp_path)
    assert status.synthesis_done(data) is False
    status.stamp_synthesis(data)
    assert status.synthesis_done(data) is True


def test_synthesis_reruns_when_validated_inputs_change(tmp_path):
    data = _setup(tmp_path)
    status.stamp_synthesis(data)
    (data / "validated" / "batch_002.json").write_text('{"observations": [1]}')
    assert status.synthesis_done(data) is False


def test_synthesis_pending_without_file(tmp_path):
    data = _setup(tmp_path)
    status.stamp_synthesis(data)
    (data / "synthesis.json").unlink()
    assert status.synthesis_done(data) is False


def test_pending_drafts_only_lists_missing_artifacts(tmp_path):
    data = tmp_path / "data"
    run = tmp_path / "run"
    (run / "artifacts").mkdir(parents=True)
    data.mkdir()
    (run / "artifacts" / "o01-a.md").write_text("done")
    opps = [
        {"opportunity_id": "o01", "above_threshold": True, "artifact_type": "sop", "artifact_path": "run/artifacts/o01-a.md"},
        {"opportunity_id": "o02", "above_threshold": True, "artifact_type": "checklist", "artifact_path": "run/artifacts/o02-b.md"},
        {"opportunity_id": "o03", "above_threshold": False, "artifact_type": "sop", "artifact_path": None},
        {"opportunity_id": "o04", "above_threshold": True, "artifact_type": "none", "artifact_path": None},
    ]
    (data / "report.json").write_text(json.dumps({"opportunities": opps}))
    assert status.pending_drafts(data, run) == ["o02"]
