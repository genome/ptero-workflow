"""shell_command_to_job

Revision ID: 2d1583cea240
Revises: 39dfaef6fd89
Create Date: 2015-08-27 13:38:05.087024

"""

# revision identifiers, used by Alembic.
revision = '2d1583cea240'
down_revision = '39dfaef6fd89'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('job',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('parameters', postgresql.JSON(), nullable=False),
            sa.Column('service_url', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['id'], ['method.id'], name=op.f('fk_job_id_method')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_job'))
            )
    op.drop_table('shell_command')


def downgrade():
    op.create_table('shell_command',
            sa.Column('id', sa.INTEGER(), nullable=False),
            sa.Column('parameters', postgresql.JSON(), autoincrement=False, nullable=False),
            sa.Column('service_url', sa.TEXT(), autoincrement=False, nullable=False),
            sa.ForeignKeyConstraint(['id'], [u'method.id'], name=u'fk_shell_command_id_method'),
            sa.PrimaryKeyConstraint('id', name=u'pk_shell_command')
            )
    op.drop_table('job')
