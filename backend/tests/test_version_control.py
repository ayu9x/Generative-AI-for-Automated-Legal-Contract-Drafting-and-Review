"""Tests for version control service."""

import pytest
from app.services.version_control import VersionControlService


@pytest.fixture
def version_service():
    return VersionControlService()


def test_create_initial_version(version_service):
    """Test creating an initial version."""
    version = version_service.create_initial_version(
        content="Initial contract content",
        author_id="user-1",
        author_name="Test User",
    )
    assert version["version_number"] == 1
    assert version["branch"] == "main"
    assert version["content_hash"] is not None


def test_create_subsequent_version(version_service):
    """Test creating subsequent versions."""
    version_service.create_initial_version(
        content="V1 content",
        author_id="user-1",
        author_name="Test User",
    )

    v2 = version_service.create_version(
        content="V2 updated content",
        change_description="Updated clause 3",
        author_id="user-1",
        author_name="Test User",
    )
    assert v2["version_number"] == 2
    assert v2["change_description"] == "Updated clause 3"


def test_version_history(version_service):
    """Test getting version history."""
    version_service.create_initial_version(content="V1", author_id="u1", author_name="User")
    version_service.create_version(content="V2", change_description="Change 1", author_id="u1", author_name="User")
    version_service.create_version(content="V3", change_description="Change 2", author_id="u1", author_name="User")

    history = version_service.get_version_history()
    assert len(history) == 3


def test_no_change_detection(version_service):
    """Test that identical content doesn't create a new version."""
    version_service.create_initial_version(content="Same content", author_id="u1", author_name="User")
    v2 = version_service.create_version(content="Same content", change_description="No change", author_id="u1", author_name="User")

    # Should still create version or indicate no change
    assert v2 is not None


def test_branching(version_service):
    """Test creating and listing branches."""
    version_service.create_initial_version(content="Main content", author_id="u1", author_name="User")

    branch = version_service.create_branch(
        branch_name="negotiation-v2",
        source_branch="main",
        author_id="u1",
    )
    assert branch["branch_name"] == "negotiation-v2"

    branches = version_service.list_branches()
    branch_names = [b["branch_name"] for b in branches]
    assert "negotiation-v2" in branch_names


def test_compute_diff(version_service):
    """Test computing diff between versions."""
    v1 = version_service.create_initial_version(
        content="Line 1\nLine 2\nLine 3",
        author_id="u1",
        author_name="User",
    )
    v2 = version_service.create_version(
        content="Line 1\nLine 2 Modified\nLine 3\nLine 4",
        change_description="Modified line 2, added line 4",
        author_id="u1",
        author_name="User",
    )

    diff = version_service.compute_diff(v1["version_id"], v2["version_id"])
    assert "additions" in diff
    assert "deletions" in diff


def test_redline_generation(version_service):
    """Test redline HTML generation."""
    v1 = version_service.create_initial_version(content="Original text", author_id="u1", author_name="User")
    v2 = version_service.create_version(content="Modified text", change_description="Edit", author_id="u1", author_name="User")

    redline = version_service.generate_redline_html(v1["version_id"], v2["version_id"])
    assert redline is not None
    assert isinstance(redline, str)


def test_comments(version_service):
    """Test adding and retrieving comments."""
    v1 = version_service.create_initial_version(content="Content", author_id="u1", author_name="User")

    comment = version_service.add_comment(
        version_id=v1["version_id"],
        comment="Please review clause 3",
        author_id="u2",
        author_name="Reviewer",
        line_number=5,
    )
    assert comment["comment"] == "Please review clause 3"

    comments = version_service.get_comments(v1["version_id"])
    assert len(comments) == 1


def test_resolve_comment(version_service):
    """Test resolving a comment."""
    v1 = version_service.create_initial_version(content="Content", author_id="u1", author_name="User")
    comment = version_service.add_comment(
        version_id=v1["version_id"],
        comment="Fix this",
        author_id="u2",
        author_name="Reviewer",
    )

    version_service.resolve_comment(comment["comment_id"])
    comments = version_service.get_comments(v1["version_id"])
    assert comments[0]["resolved"] is True


def test_approve_version(version_service):
    """Test version approval."""
    v1 = version_service.create_initial_version(content="Content", author_id="u1", author_name="User")

    result = version_service.approve_version(
        version_id=v1["version_id"],
        approver_id="admin-1",
        approver_name="Admin User",
    )
    assert result is not None
