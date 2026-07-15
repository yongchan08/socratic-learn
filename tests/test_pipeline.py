from concurrent.futures import Future

import pytest

from socratic_tutor.pipeline import QuestionGenerationTimeoutError, _collect_question_results


def test_collect_question_results_times_out_and_cancels_pending_future():
    pending = Future()

    with pytest.raises(QuestionGenerationTimeoutError, match="제한 시간"):
        _collect_question_results({pending: 1}, total=1, on_progress=None, timeout_seconds=0.001)

    assert pending.cancelled()
