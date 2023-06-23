"""Initial migration.

Revision ID: eb2729829d81
Revises: 
Create Date: 2023-06-22 20:02:11.456057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb2729829d81'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('long_link', sa.String(), nullable=True),
    sa.Column('short_link', sa.String(length=10), nullable=True),
    sa.Column('custom_link', sa.String(length=50), nullable=True),
    sa.Column('clicks', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('custom_link'),
    sa.UniqueConstraint('short_link')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('links')
    op.drop_table('users')
    # ### end Alembic commands ###