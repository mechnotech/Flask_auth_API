"""empty message

Revision ID: cb69d4ce62c6
Revises: 256dd0d6b5ad
Create Date: 2021-12-20 15:16:00.723025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb69d4ce62c6'
down_revision = '256dd0d6b5ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f('uq__jwt__id'), 'jwt', ['id'])
    op.create_unique_constraint(op.f('uq__logins__id'), 'logins', ['id'])
    op.create_unique_constraint(op.f('uq__profiles__id'), 'profiles', ['id'])
    op.create_unique_constraint(op.f('uq__roles__id'), 'roles', ['id'])
    op.create_unique_constraint(op.f('uq__users__id'), 'users', ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq__users__id'), 'users', type_='unique')
    op.drop_constraint(op.f('uq__roles__id'), 'roles', type_='unique')
    op.drop_constraint(op.f('uq__profiles__id'), 'profiles', type_='unique')
    op.drop_constraint(op.f('uq__logins__id'), 'logins', type_='unique')
    op.drop_constraint(op.f('uq__jwt__id'), 'jwt', type_='unique')
    # ### end Alembic commands ###
