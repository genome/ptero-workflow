"""execution_indexes

Revision ID: 1f093e84c2b5
Revises: 2d1583cea240
Create Date: 2015-09-06 02:58:51.574150

"""

# revision identifiers, used by Alembic.
revision = '1f093e84c2b5'
down_revision = '2d1583cea240'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index(op.f('ix_execution_status'), 'execution', ['status'], unique=False)
    op.create_index(op.f('ix_execution_type'), 'execution', ['type'], unique=False)
    op.create_index(op.f('ix_execution_status_history_execution_id'), 'execution_status_history', ['execution_id'], unique=False)
    op.create_index(op.f('ix_execution_status_history_timestamp'), 'execution_status_history', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_execution_status_history_timestamp'), table_name='execution_status_history')
    op.drop_index(op.f('ix_execution_status_history_execution_id'), table_name='execution_status_history')
    op.drop_index(op.f('ix_execution_type'), table_name='execution')
    op.drop_index(op.f('ix_execution_status'), table_name='execution')
