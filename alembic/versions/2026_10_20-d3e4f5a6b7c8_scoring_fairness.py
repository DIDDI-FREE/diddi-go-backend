"""Make public driver ratings reflect completed-ride ratings only.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-10-20
"""

from alembic import op
import sqlalchemy as sa


revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "driver_profiles",
        "rating_avg",
        existing_type=sa.Numeric(precision=3, scale=2),
        nullable=True,
        schema="ride",
    )
    # Keep every historical rating row. Only the denormalized display cache is
    # rebuilt from ratings that would be accepted under the current rules.
    op.execute(
        """
        UPDATE ride.driver_profiles AS driver
        SET
            rating_count = COALESCE(summary.rating_count, 0),
            rating_avg = summary.rating_avg
        FROM (
            SELECT
                driver_profile.id AS driver_id,
                COUNT(rating.id)::integer AS rating_count,
                AVG(rating.rating)::numeric(3, 2) AS rating_avg
            FROM ride.driver_profiles AS driver_profile
            LEFT JOIN ride.rides AS ride
                ON ride.driver_id = driver_profile.id
                AND ride.status = 'completed'
            LEFT JOIN ride.ride_ratings AS rating
                ON rating.ride_id = ride.id
                AND rating.rater_role = 'passenger'
            GROUP BY driver_profile.id
        ) AS summary
        WHERE driver.id = summary.driver_id
        """
    )


def downgrade() -> None:
    op.execute("UPDATE ride.driver_profiles SET rating_avg = 5.00 WHERE rating_avg IS NULL")
    op.alter_column(
        "driver_profiles",
        "rating_avg",
        existing_type=sa.Numeric(precision=3, scale=2),
        nullable=False,
        schema="ride",
    )
