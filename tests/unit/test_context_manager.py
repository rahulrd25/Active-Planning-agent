import pytest
from services.context_manager import (
    count_tokens,
    should_compress,
    split_messages,
    maybe_compress,
)
import services.context_manager as cm


# ── fixtures ──────────────────────────────────

@pytest.fixture
def short_messages():
    return [
        {"role": "user", "content": "I want to build a website"},
        {"role": "assistant", "content": "Sure, let me help you plan that."},
    ]


@pytest.fixture
def long_messages():
    """Simulate a long conversation with many messages."""
    messages = []
    for i in range(20):
        messages.append({"role": "user", "content": f"This is user message number {i} with some content to add tokens"})
        messages.append({"role": "assistant", "content": f"This is assistant response number {i} with detailed information"})
    return messages


# ── count_tokens tests ────────────────────────

def test_count_tokens_returns_int(short_messages):
    count = count_tokens(short_messages)
    assert isinstance(count, int)


def test_count_tokens_returns_positive(short_messages):
    count = count_tokens(short_messages)
    assert count > 0


def test_count_tokens_empty_messages():
    count = count_tokens([])
    assert count == 0


def test_count_tokens_more_messages_more_tokens(short_messages, long_messages):
    short_count = count_tokens(short_messages)
    long_count = count_tokens(long_messages)
    assert long_count > short_count


# ── should_compress tests ─────────────────────

def test_should_compress_below_threshold():
    assert should_compress(1000) is False


def test_should_compress_at_threshold():
    assert should_compress(6000) is True


def test_should_compress_above_threshold():
    assert should_compress(7000) is True


# ── split_messages tests ──────────────────────

def test_split_messages_old_is_60_percent(long_messages):
    old, recent = split_messages(long_messages)
    expected_split = int(len(long_messages) * 0.6)
    assert len(old) == expected_split


def test_split_messages_recent_is_40_percent(long_messages):
    old, recent = split_messages(long_messages)
    assert len(old) + len(recent) == len(long_messages)


def test_split_messages_preserves_all_messages(long_messages):
    old, recent = split_messages(long_messages)
    assert len(old) + len(recent) == len(long_messages)


# ── maybe_compress tests ──────────────────────

def test_maybe_compress_no_compression_needed(short_messages):
    result_messages, summary = maybe_compress(short_messages)
    assert summary is None
    assert result_messages == short_messages


def test_maybe_compress_triggers_compression(long_messages):
    # force compression by lowering threshold
    original_threshold = cm.COMPRESSION_THRESHOLD
    cm.COMPRESSION_THRESHOLD = 10

    result_messages, summary = maybe_compress(long_messages)

    cm.COMPRESSION_THRESHOLD = original_threshold

    assert summary is not None
    assert len(result_messages) < len(long_messages)


def test_maybe_compress_summary_is_string(long_messages):
    original_threshold = cm.COMPRESSION_THRESHOLD
    cm.COMPRESSION_THRESHOLD = 10

    _, summary = maybe_compress(long_messages)

    cm.COMPRESSION_THRESHOLD = original_threshold
    assert isinstance(summary, str)
    assert len(summary) > 0