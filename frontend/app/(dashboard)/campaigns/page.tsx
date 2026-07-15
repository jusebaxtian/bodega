"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type CampaignRankingItem = {
  campaign_id: string;
  name: string;
  score: number;
  health_status: string;
};

const HEALTH_COLORS: Record<string, string> = {
  excelente: "bg-emerald-500/15 text-emerald-400",
  buena: "bg-primary/15 text-primary",
  atencion: "bg-amber-500/15 text-amber-400",
  critica: "bg-danger/15 text-danger",
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<CampaignRankingItem[] | null>(null);

  useEffect(() => {
    (async () => {
      const accounts = await apiFetch("/api/v1/ad-accounts");
      if (accounts.length === 0) {
        setCampaigns([]);
        return;
      }
      const summary = await apiFetch(`/api/v1/ad-accounts/${accounts[0].id}/dashboard-summary`);
      const all = [...summary.best_campaigns, ...summary.critical_campaigns];
      const unique = Array.from(new Map(all.map((c: CampaignRankingItem) => [c.campaign_id, c])).values());
      setCampaigns(unique);
    })();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-1">Campañas</h1>
      <p className="text-sm text-foreground/60 mb-6">Puntuación IA (0-100) y estado de salud de cada campaña.</p>

      <div className="rounded-lg border border-border divide-y divide-border">
        {campaigns === null && <p className="p-4 text-sm text-foreground/60">Cargando...</p>}
        {campaigns?.length === 0 && <p className="p-4 text-sm text-foreground/60">No hay campañas todavía.</p>}
        {campaigns?.map((c) => (
          <Link key={c.campaign_id} href={`/campaigns/${c.campaign_id}`} className="flex items-center justify-between p-4 hover:bg-muted">
            <span className="text-sm font-medium">{c.name}</span>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold">{c.score}</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${HEALTH_COLORS[c.health_status] ?? ""}`}>
                {c.health_status}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
