"""add leetcode sync schema

Revision ID: 202606030001
Revises: 202605300001
Create Date: 2026-06-03 00:01:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606030001"
down_revision: str | None = "202605300001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leetcode_profiles", sa.Column("last_sync_attempted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "leetcode_profiles",
        sa.Column("sync_status", sa.String(length=32), server_default="never_synced", nullable=False),
    )
    op.add_column("leetcode_profiles", sa.Column("last_sync_error", sa.String(length=512), nullable=True))
    op.create_index("ix_leetcode_profiles_sync_status", "leetcode_profiles", ["sync_status"])

    op.add_column("user_submissions", sa.Column("leetcode_submission_id", sa.String(length=64), nullable=True))
    op.add_column(
        "user_submissions",
        sa.Column("source", sa.String(length=32), server_default="leetcode", nullable=False),
    )

    op.create_unique_constraint(
        "uq_user_submissions_user_leetcode_submission_id",
        "user_submissions",
        ["user_id", "leetcode_submission_id"],
    )

    op.create_index("ix_user_submissions_user_submitted_at", "user_submissions", ["user_id", "submitted_at"])
    op.create_index("ix_user_submissions_user_status", "user_submissions", ["user_id", "status"])
    op.create_index("ix_user_submissions_user_language", "user_submissions", ["user_id", "language"])
    op.create_index("ix_user_submissions_problem_submitted_at", "user_submissions", ["problem_id", "submitted_at"])


def downgrade() -> None:
    op.drop_index("ix_user_submissions_problem_submitted_at", table_name="user_submissions")
    op.drop_index("ix_user_submissions_user_language", table_name="user_submissions")
    op.drop_index("ix_user_submissions_user_status", table_name="user_submissions")
    op.drop_index("ix_user_submissions_user_submitted_at", table_name="user_submissions")

    op.drop_constraint(
        "uq_user_submissions_user_leetcode_submission_id",
        "user_submissions",
        type_="unique",
    )

    op.drop_column("user_submissions", "source")
    op.drop_column("user_submissions", "leetcode_submission_id")

    op.drop_index("ix_leetcode_profiles_sync_status", table_name="leetcode_profiles")
    op.drop_column("leetcode_profiles", "last_sync_error")
    op.drop_column("leetcode_profiles", "sync_status")
    op.drop_column("leetcode_profiles", "last_sync_attempted_at")
