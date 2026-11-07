from __future__ import annotations

from northstar_helpdesk.evaluation import run_evaluations


def test_evaluation_suite_runs(agent):
    results = run_evaluations(agent)

    assert len(results) == 3
    assert all("latency_ms" in result for result in results)
    assert all(0 <= result["answer_score"] <= 1 for result in results)
