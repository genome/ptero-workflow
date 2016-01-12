"""set_backfilled_execution_columns_non_nullable

Revision ID: 2b63dddbaa74
Revises: 5005862095e3
Create Date: 2016-01-12 00:07:02.830292

"""

# revision identifiers, used by Alembic.
revision = '2b63dddbaa74'
down_revision = '5005862095e3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('execution', 'timestamp',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
    op.alter_column('execution_status_history', 'workflow_id',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade():
    op.alter_column('execution_status_history', 'workflow_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('execution', 'timestamp',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)
