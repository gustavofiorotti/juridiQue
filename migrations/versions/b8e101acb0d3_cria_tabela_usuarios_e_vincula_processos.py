"""Cria tabela usuarios e vincula processos

Revision ID: b8e101acb0d3
Revises: 
Create Date: 2026-05-26 21:34:37.178133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8e101acb0d3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Cria a tabela de usuários
    op.create_table('usuarios',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('senha_hash', sa.String(length=256), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_usuarios_email'), ['email'], unique=True)

    # 2. Altera a tabela preexistente 'processos_judiciais' no schema 'dbo'
    # vinculando a Foreign Key e atualizando os campos necessários
    with op.batch_alter_table('processos_judiciais', schema='dbo') as batch_op:
        batch_op.alter_column('id_usuario',
               existing_type=sa.VARCHAR(length=255, collation='Latin1_General_100_CI_AI'),
               type_=sa.String(length=36),
               existing_nullable=True)
        batch_op.alter_column('data_submissao',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.create_foreign_key('fk_processos_usuarios', 'usuarios', ['id_usuario'], ['id'])


def downgrade():
    # 1. Remove as alterações da tabela 'processos_judiciais' no schema 'dbo'
    with op.batch_alter_table('processos_judiciais', schema='dbo') as batch_op:
        batch_op.drop_constraint('fk_processos_usuarios', type_='foreignkey')
        batch_op.alter_column('data_submissao',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('id_usuario',
               existing_type=sa.String(length=36),
               type_=sa.VARCHAR(length=255, collation='Latin1_General_100_CI_AI'),
               existing_nullable=True)

    # 2. Dropa a tabela 'usuarios'
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_usuarios_email'))

    op.drop_table('usuarios')
