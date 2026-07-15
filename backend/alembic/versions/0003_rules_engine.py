"""rules engine: rules, recommendations, campaign_scores

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("conditions", postgresql.JSONB, nullable=False),
        sa.Column("action_type", sa.String, nullable=False),
        sa.Column("priority", sa.String, nullable=False, server_default="media"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ad_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("priority", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("reason", sa.String, nullable=False),
        sa.Column("confidence", sa.Integer, nullable=False),
        sa.Column("action_type", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_recommendations_entity", "recommendations", ["entity_type", "entity_id"])

    op.create_table(
        "campaign_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("health_status", sa.String, nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    for table in ("rules", "recommendations", "campaign_scores"):
        op.execute(f"alter table public.{table} enable row level security")

    op.execute(
        """
        create policy "rules_select_global_or_own_org" on public.rules
          for select using (
            org_id is null
            or exists (select 1 from public.org_members m where m.org_id = rules.org_id and m.user_id = auth.uid())
          )
        """
    )
    op.execute(
        """
        create policy "recommendations_select_member" on public.recommendations
          for select using (
            exists (
              select 1 from public.ad_accounts a
              join public.org_members m on m.org_id = a.org_id
              where a.id = recommendations.ad_account_id and m.user_id = auth.uid()
            )
          )
        """
    )
    op.execute(
        """
        create policy "campaign_scores_select_member" on public.campaign_scores
          for select using (
            exists (
              select 1 from public.campaigns c
              join public.ad_accounts a on a.id = c.ad_account_id
              join public.org_members m on m.org_id = a.org_id
              where c.id = campaign_scores.campaign_id and m.user_id = auth.uid()
            )
          )
        """
    )


def downgrade() -> None:
    op.drop_table("campaign_scores")
    op.drop_table("recommendations")
    op.drop_table("rules")
