"""empty message

Revision ID: 169de9909027
Revises: 962157a992d7
Create Date: 2024-12-03 23:05:49.525918

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '169de9909027'
down_revision = '962157a992d7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('incorrect_answer')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('incorrect_answer', mysql.TEXT(), nullable=True))

    # ### end Alembic commands ###