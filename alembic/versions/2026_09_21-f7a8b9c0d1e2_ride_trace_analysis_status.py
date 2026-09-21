"""Persist the outcome and quality of DiddiMap trace analysis.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-09-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: str | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("trace_analysis_status", sa.String(30), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("trace_analysis_error_code", sa.String(80), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("trace_recommendation", sa.String(80), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("trace_quality_label", sa.String(40), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("trace_quality_score", sa.Numeric(5, 4), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("trace_points_count", sa.Integer(), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("trace_usable_points_count", sa.Integer(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("rides", "trace_usable_points_count", schema="ride")
    op.drop_column("rides", "trace_points_count", schema="ride")
    op.drop_column("rides", "trace_quality_score", schema="ride")
    op.drop_column("rides", "trace_quality_label", schema="ride")
    op.drop_column("rides", "trace_recommendation", schema="ride")
    op.drop_column("rides", "trace_analysis_error_code", schema="ride")
    op.drop_column("rides", "trace_analysis_status", schema="ride")
