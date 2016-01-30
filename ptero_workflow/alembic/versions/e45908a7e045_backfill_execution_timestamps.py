"""backfill_execution_timestamps

Revision ID: e45908a7e045
Revises: 539a0ab6e387
Create Date: 2016-01-11 20:22:54.465744

"""

# revision identifiers, used by Alembic.
revision = 'e45908a7e045'
down_revision = '539a0ab6e387'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""
            UPDATE execution e
            SET timestamp = esh.timestamp
            FROM execution_status_history esh
                WHERE e.id = esh.execution_id
                AND esh.status = 'new';
    """)


def downgrade():
    pass
