"""meta ads integration: campaigns, ad_sets, ads, insight_snapshots, sync_jobs

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-15

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ad_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meta_campaign_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("objective", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("daily_budget", sa.Numeric, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_campaigns_account_meta_id", "campaigns", ["ad_account_id", "meta_campaign_id"])

    op.create_table(
        "ad_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meta_adset_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("targeting_summary", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_ad_sets_campaign_meta_id", "ad_sets", ["campaign_id", "meta_adset_id"])

    op.create_table(
        "ads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ad_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ad_sets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meta_ad_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("creative_type", sa.String, nullable=True),
        sa.Column("creative_preview_url", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_ads_adset_meta_id", "ads", ["ad_set_id", "meta_ad_id"])

    op.create_table(
        "insight_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ad_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("spend", sa.Numeric, nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ctr", sa.Numeric, nullable=False, server_default="0"),
        sa.Column("cpc", sa.Numeric, nullable=False, server_default="0"),
        sa.Column("cpm", sa.Numeric, nullable=False, server_default="0"),
        sa.Column("cpl", sa.Numeric, nullable=True),
        sa.Column("cpa", sa.Numeric, nullable=True),
        sa.Column("roas", sa.Numeric, nullable=True),
        sa.Column("conversions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("frequency", sa.Numeric, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_insight_snapshots_ad_date", "insight_snapshots", ["ad_id", "snapshot_date"])

    op.create_table(
        "sync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ad_account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    for table in ("campaigns", "ad_sets", "ads", "insight_snapshots", "sync_jobs"):
        op.execute(f"alter table public.{table} enable row level security")

    op.execute(
        """
        create policy "campaigns_select_member" on public.campaigns
          for select using (
            exists (
              select 1 from public.ad_accounts a
              join public.org_members m on m.org_id = a.org_id
              where a.id = campaigns.ad_account_id and m.user_id = auth.uid()
            )
          )
        """
    )
    op.execute(
        """
        create policy "ad_sets_select_member" on public.ad_sets
          for select using (
            exists (
              select 1 from public.campaigns c
              join public.ad_accounts a on a.id = c.ad_account_id
              join public.org_members m on m.org_id = a.org_id
              where c.id = ad_sets.campaign_id and m.user_id = auth.uid()
            )
          )
        """
    )
    op.execute(
        """
        create policy "ads_select_member" on public.ads
          for select using (
            exists (
              select 1 from public.ad_sets s
              join public.campaigns c on c.id = s.campaign_id
              join public.ad_accounts a on a.id = c.ad_account_id
              join public.org_members m on m.org_id = a.org_id
              where s.id = ads.ad_set_id and m.user_id = auth.uid()
            )
          )
        """
    )
    op.execute(
        """
        create policy "insight_snapshots_select_member" on public.insight_snapshots
          for select using (
            exists (
              select 1 from public.ads ad
              join public.ad_sets s on s.id = ad.ad_set_id
              join public.campaigns c on c.id = s.campaign_id
              join public.ad_accounts a on a.id = c.ad_account_id
              join public.org_members m on m.org_id = a.org_id
              where ad.id = insight_snapshots.ad_id and m.user_id = auth.uid()
            )
          )
        """
    )
    op.execute(
        """
        create policy "sync_jobs_select_member" on public.sync_jobs
          for select using (
            exists (
              select 1 from public.ad_accounts a
              join public.org_members m on m.org_id = a.org_id
              where a.id = sync_jobs.ad_account_id and m.user_id = auth.uid()
            )
          )
        """
    )


def downgrade() -> None:
    op.drop_table("sync_jobs")
    op.drop_table("insight_snapshots")
    op.drop_table("ads")
    op.drop_table("ad_sets")
    op.drop_table("campaigns")
