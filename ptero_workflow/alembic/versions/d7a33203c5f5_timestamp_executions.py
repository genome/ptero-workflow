"""timestamp_executions

Revision ID: d7a33203c5f5
Revises: 4f5b26bea9d
Create Date: 2016-01-10 04:21:13.111336

"""

# revision identifiers, used by Alembic.
revision = 'd7a33203c5f5'
down_revision = '4f5b26bea9d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('execution', sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_execution_timestamp'), 'execution', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_execution_timestamp'), table_name='execution')
    op.drop_column('execution', 'timestamp')
