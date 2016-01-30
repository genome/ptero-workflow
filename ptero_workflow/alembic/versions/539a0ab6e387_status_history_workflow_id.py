"""status_history_workflow_id

Revision ID: 539a0ab6e387
Revises: d7a33203c5f5
Create Date: 2016-01-10 06:38:41.668535

"""

# revision identifiers, used by Alembic.
revision = '539a0ab6e387'
down_revision = 'd7a33203c5f5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('execution_status_history', sa.Column('workflow_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_execution_status_history_workflow_id'), 'execution_status_history', ['workflow_id'], unique=False)
    op.create_foreign_key(op.f('fk_execution_status_history_workflow_id_workflow'), 'execution_status_history', 'workflow', ['workflow_id'], ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint(op.f('fk_execution_status_history_workflow_id_workflow'), 'execution_status_history', type_='foreignkey')
    op.drop_index(op.f('ix_execution_status_history_workflow_id'), table_name='execution_status_history')
    op.drop_column('execution_status_history', 'workflow_id')
