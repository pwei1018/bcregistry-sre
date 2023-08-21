"""add_callback

Revision ID: 6179cd10fa94
Revises: ab887fe3402f
Create Date: 2023-08-11 15:05:46.818892

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6179cd10fa94'
down_revision = 'ab887fe3402f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notification_history', sa.Column('gc_notify_response_id', sa.String, nullable=True))
    op.add_column('notification_history', sa.Column('gc_notify_status', sa.String, nullable=True))

    op.create_table('gc_notify_callback',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('notify_id', sa.String),
                    sa.Column('reference', sa.String),
                    sa.Column('to', sa.String),
                    sa.Column('status', sa.String),
                    sa.Column('status_description', sa.String),
                    sa.Column('provider_response', sa.String),
                    sa.Column('created_at', sa.DateTime()),
                    sa.Column('updated_at', sa.DateTime()),
                    sa.Column('completed_at', sa.DateTime()),
                    sa.Column('sent_at', sa.DateTime()),
                    sa.Column('notification_type', sa.String),
                    sa.PrimaryKeyConstraint('id')
                    )

def downgrade():
    op.drop_table('gc_notify_callback')

    op.drop_column('notification_history', 'gc_notify_response_id')
    op.drop_column('notification_history', 'gc_notify_status')
