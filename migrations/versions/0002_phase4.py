"""Phase 4 schema: conversations + messages tables, model/tokens on usage_logs.

Revision ID: 0002_phase4
Revises: 0001_initial
Create Date: 2026-10-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_phase4"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_conversations_key_id", "conversations", ["key_id"])
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.add_column("usage_logs", sa.Column("model", sa.String(120), nullable=True))
    op.add_column("usage_logs", sa.Column("tokens", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("usage_logs", "tokens")
    op.drop_column("usage_logs", "model")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_index("ix_conversations_key_id", table_name="conversations")
    op.drop_table("conversations")
