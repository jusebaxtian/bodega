"""ai layer: ai_explanations

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-15

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_explanations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("main_problem", sa.String, nullable=False),
        sa.Column("severity", sa.String, nullable=False),
        sa.Column("diagnosis", sa.String, nullable=False),
        sa.Column("immediate_actions", postgresql.JSONB, nullable=False),
        sa.Column("actions_72h", postgresql.JSONB, nullable=False),
        sa.Column("confidence", sa.Integer, nullable=False),
        sa.Column("explanation_simple", sa.String, nullable=False),
        sa.Column("model_used", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_explanations_entity", "ai_explanations", ["entity_type", "entity_id"])

    op.execute("alter table public.ai_explanations enable row level security")
    op.execute(
        """
        create policy "ai_explanations_select_via_ad" on public.ai_explanations
          for select using (
            entity_type <> 'ad'
            or exists (
              select 1 from public.ads ad
              join public.ad_sets s on s.id = ad.ad_set_id
              join public.campaigns c on c.id = s.campaign_id
              join public.ad_accounts a on a.id = c.ad_account_id
              join public.org_members m on m.org_id = a.org_id
              where ad.id = ai_explanations.entity_id and m.user_id = auth.uid()
            )
          )
        """
    )


def downgrade() -> None:
    op.drop_table("ai_explanations")
