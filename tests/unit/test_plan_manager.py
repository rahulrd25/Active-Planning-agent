import pytest
from models.plan import Plan, PlanStep
from services.plan_manager import (
    create_plan,
    add_step,
    edit_step,
    remove_step,
    reorder_steps,
    diff_plans,
    snapshot_plan
)


# ── fixtures ──────────────────────────────────

@pytest.fixture
def sample_plan():
    """Creates a basic plan for testing."""
    return create_plan(
        title="Test Plan",
        steps_data=[
            {"title": "Step One", "description": "First step"},
            {"title": "Step Two", "description": "Second step"},
            {"title": "Step Three", "description": "Third step"},
        ]
    )


# ── create_plan tests ─────────────────────────

def test_create_plan_has_correct_title(sample_plan):
    assert sample_plan.title == "Test Plan"


def test_create_plan_has_correct_step_count(sample_plan):
    assert len(sample_plan.steps) == 3


def test_create_plan_steps_have_correct_order(sample_plan):
    orders = [s.order for s in sample_plan.steps]
    assert orders == [1, 2, 3]


def test_create_plan_generates_unique_ids(sample_plan):
    ids = [s.id for s in sample_plan.steps]
    assert len(ids) == len(set(ids))  # no duplicates


def test_create_plan_version_starts_at_one(sample_plan):
    assert sample_plan.version == 1


# ── add_step tests ────────────────────────────

def test_add_step_increases_count(sample_plan):
    updated = add_step(sample_plan, "Step Four", "Fourth step")
    assert len(updated.steps) == 4


def test_add_step_has_correct_order(sample_plan):
    updated = add_step(sample_plan, "Step Four", "Fourth step")
    assert updated.steps[-1].order == 4


def test_add_step_has_correct_title(sample_plan):
    updated = add_step(sample_plan, "Step Four", "Fourth step")
    assert updated.steps[-1].title == "Step Four"


def test_add_step_without_description(sample_plan):
    updated = add_step(sample_plan, "Step Four")
    assert updated.steps[-1].description == ""


# ── edit_step tests ───────────────────────────

def test_edit_step_title(sample_plan):
    step_id = sample_plan.steps[0].id
    updated = edit_step(sample_plan, step_id, title="Updated Title")
    assert updated.steps[0].title == "Updated Title"


def test_edit_step_description(sample_plan):
    step_id = sample_plan.steps[0].id
    updated = edit_step(sample_plan, step_id, description="Updated description")
    assert updated.steps[0].description == "Updated description"


def test_edit_step_does_not_affect_other_steps(sample_plan):
    step_id = sample_plan.steps[0].id
    updated = edit_step(sample_plan, step_id, title="Updated Title")
    assert updated.steps[1].title == "Step Two"
    assert updated.steps[2].title == "Step Three"


# ── remove_step tests ─────────────────────────

def test_remove_step_decreases_count(sample_plan):
    step_id = sample_plan.steps[0].id
    updated = remove_step(sample_plan, step_id)
    assert len(updated.steps) == 2


def test_remove_step_reorders_correctly(sample_plan):
    step_id = sample_plan.steps[0].id
    updated = remove_step(sample_plan, step_id)
    orders = [s.order for s in updated.steps]
    assert orders == [1, 2]


def test_remove_step_keeps_correct_steps(sample_plan):
    step_id = sample_plan.steps[0].id
    updated = remove_step(sample_plan, step_id)
    titles = [s.title for s in updated.steps]
    assert "Step One" not in titles
    assert "Step Two" in titles


# ── diff_plans tests ──────────────────────────

def test_diff_detects_added_step(sample_plan):
    old_snapshot = snapshot_plan(sample_plan, "before")
    updated = add_step(sample_plan, "New Step", "New description")
    diff = diff_plans(old_snapshot.plan, updated)
    assert len(diff.added) == 1
    assert diff.added[0].title == "New Step"


def test_diff_detects_removed_step(sample_plan):
    old_snapshot = snapshot_plan(sample_plan, "before")
    step_id = sample_plan.steps[0].id
    updated = remove_step(sample_plan, step_id)
    diff = diff_plans(old_snapshot.plan, updated)
    assert len(diff.removed) == 1


def test_diff_no_changes(sample_plan):
    old_snapshot = snapshot_plan(sample_plan, "before")
    diff = diff_plans(old_snapshot.plan, sample_plan)
    assert diff.change_summary == "No changes"


# ── snapshot_plan tests ───────────────────────

def test_snapshot_preserves_plan(sample_plan):
    version = snapshot_plan(sample_plan, "initial")
    assert version.plan.title == sample_plan.title
    assert len(version.plan.steps) == len(sample_plan.steps)


def test_snapshot_is_independent_copy(sample_plan):
    version = snapshot_plan(sample_plan, "initial")
    # modify original — snapshot should not change
    sample_plan.steps[0].title = "Modified"
    assert version.plan.steps[0].title == "Step One"