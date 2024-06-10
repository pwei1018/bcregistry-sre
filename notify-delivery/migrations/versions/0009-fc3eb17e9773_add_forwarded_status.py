"""add FORWARDED status

Revision ID: fc3eb17e9773
Revises: 6179cd10fa94
Create Date: 2024-01-04 10:26:43.221346

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, String
from sqlalchemy.sql import column, table


# revision identifiers, used by Alembic.
revision = "fc3eb17e9773"
down_revision = "6179cd10fa94"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO notification_status VALUES('FORWARDED','Status for the notification forwarded to SMTP service', false)"
    )


def downgrade():
    op.execute("DELETE notification_status WHERE code='FORWARDED'")
