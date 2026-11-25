"""Keep the Rewards quote reference and the offer shown to the customer (ticket 040).

- ``ride_quotes.rewards_quote_id``: the Rewards quote, sent back at reserve so Rewards
  gives the quoted discount (decision of 2026-11-25, point 1).
- ``ride_quotes.rewards_offer`` / ``rides.rewards_offer``: the offer block relayed by
  Rewards, frozen on the ride when it is ordered (point 3).

Only nullable columns are added: old rows stay valid, no backfill.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ride_quotes", sa.Column("rewards_quote_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("ride_quotes", sa.Column("rewards_offer", JSONB(), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("rewards_offer", JSONB(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("rides", "rewards_offer", schema="ride")
    op.drop_column("ride_quotes", "rewards_offer", schema="ride")
    op.drop_column("ride_quotes", "rewards_quote_id", schema="ride")
