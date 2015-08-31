"""empty message

Revision ID: 39dfaef6fd89
Revises: 177e0b42a8c3
Create Date: 2015-08-27 09:30:24.189952

"""

# revision identifiers, used by Alembic.
revision = '39dfaef6fd89'
down_revision = '177e0b42a8c3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('shell_command', sa.Column('service_url', sa.Text(), nullable=False))


def downgrade():
    op.drop_column('shell_command', 'service_url')
