"""Add five vehicle KYV photo views

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-09-07 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "c4d5e6f7a8b9"
down_revision: str | None = "b3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("vehicle_front_photo_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_back_photo_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_left_photo_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_right_photo_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_interior_photo_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_front_photo_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_back_photo_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_left_photo_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_right_photo_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_interior_photo_url", sa.Text(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("vehicles", "vehicle_interior_photo_url", schema="ride")
    op.drop_column("vehicles", "vehicle_right_photo_url", schema="ride")
    op.drop_column("vehicles", "vehicle_left_photo_url", schema="ride")
    op.drop_column("vehicles", "vehicle_back_photo_url", schema="ride")
    op.drop_column("vehicles", "vehicle_front_photo_url", schema="ride")
    op.drop_column("vehicles", "vehicle_interior_photo_file_id", schema="ride")
    op.drop_column("vehicles", "vehicle_right_photo_file_id", schema="ride")
    op.drop_column("vehicles", "vehicle_left_photo_file_id", schema="ride")
    op.drop_column("vehicles", "vehicle_back_photo_file_id", schema="ride")
    op.drop_column("vehicles", "vehicle_front_photo_file_id", schema="ride")
