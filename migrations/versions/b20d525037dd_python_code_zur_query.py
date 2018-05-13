"""python code zur query

Revision ID: b20d525037dd
Revises: 7e9a498dc3c7
Create Date: 2018-05-13 21:40:41.919944

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b20d525037dd'
down_revision = '7e9a498dc3c7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sparql', sa.Column('pythonscript', sa.String(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sparql', 'pythonscript')
    # ### end Alembic commands ###
