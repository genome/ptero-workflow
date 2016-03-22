"""store_service_data

Revision ID: 89b1fb28bb6c
Revises: 2b63dddbaa74
Create Date: 2016-03-21 20:13:39.549582

"""

# revision identifiers, used by Alembic.
revision = '89b1fb28bb6c'
down_revision = '2b63dddbaa74'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('job', sa.Column('service_data_to_save', postgresql.JSON(), nullable=False))


def downgrade():
    op.drop_column('job', 'service_data_to_save')
