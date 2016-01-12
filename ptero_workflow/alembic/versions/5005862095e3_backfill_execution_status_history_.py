"""backfill_execution_status_history_workflow_id

Revision ID: 5005862095e3
Revises: e45908a7e045
Create Date: 2016-01-11 23:57:51.644206

"""

# revision identifiers, used by Alembic.
revision = '5005862095e3'
down_revision = 'e45908a7e045'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""
            UPDATE execution_status_history esh
            SET workflow_id = e.workflow_id
            FROM execution e
                WHERE e.id = esh.execution_id;
    """)


def downgrade():
    pass
