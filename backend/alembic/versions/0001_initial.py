"""initial schema: orgs, org_members, ad_accounts

Revision ID: 0001
Revises:
Create Date: 2026-07-15

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orgs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "org_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String, nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_org_members_org_user", "org_members", ["org_id", "user_id"])

    op.create_table(
        "ad_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meta_account_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("connected_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_token_encrypted", sa.String, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # RLS: solo miembros de la org pueden ver/tocar sus propias filas
    op.execute("alter table public.orgs enable row level security")
    op.execute("alter table public.org_members enable row level security")
    op.execute("alter table public.ad_accounts enable row level security")

    op.execute(
        """
        create policy "orgs_select_member" on public.orgs
          for select using (
            exists (select 1 from public.org_members m where m.org_id = orgs.id and m.user_id = auth.uid())
          )
        """
    )
    op.execute(
        """
        create policy "org_members_select_own_org" on public.org_members
          for select using (
            exists (select 1 from public.org_members m where m.org_id = org_members.org_id and m.user_id = auth.uid())
          )
        """
    )
    op.execute(
        """
        create policy "ad_accounts_select_member" on public.ad_accounts
          for select using (
            exists (select 1 from public.org_members m where m.org_id = ad_accounts.org_id and m.user_id = auth.uid())
          )
        """
    )


def downgrade() -> None:
    op.drop_table("ad_accounts")
    op.drop_table("org_members")
    op.drop_table("orgs")
