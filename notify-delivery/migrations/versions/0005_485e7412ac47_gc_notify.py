"""gc notify

Revision ID: 485e7412ac47
Revises: aa4e6bdf1984
Create Date: 2022-05-18 03:52:03.494871

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, String
from sqlalchemy.sql import column, table


# revision identifiers, used by Alembic.
revision = '485e7412ac47'
down_revision = 'aa4e6bdf1984'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('notification_provider',
                    sa.Column('code', sa.String(length=15), nullable=False),
                    sa.Column('desc', sa.String(length=100), nullable=True),
                    sa.Column('default', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('code')
                    )    
    notification_provider_table = table('notification_provider',
                                    column('code', String),
                                    column('desc', String),
                                    column('default', Boolean)
                                    )

    op.bulk_insert(
        notification_provider_table,
        [
            {'code': 'SMTP', 'desc': 'Delivery Email by SMTP service', 'default': True},
            {'code': 'GC_NOTIFY', 'desc': 'Delivery by GC Notify service', 'default': False}
        ]
    )

    op.add_column('notification', sa.Column('provider_code',  sa.String(length=15), nullable=True))
    op.create_foreign_key(None, 'notification', 'notification_provider', ['provider_code'], ['code'])


def downgrade():
    op.drop_column('notification', 'provider_code')
    op.drop_table('notification_provider')
    