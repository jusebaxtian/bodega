"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, DollarSign, MousePointerClick, Target } from "lucide-react";
import { apiFetch } from "@/lib/api";

type CampaignRankingItem = {
  campaign_id: string;
  name: string;
  score: number;
  health_status: string;
};

type Alert = {
  id: string;
  title: string;
  priority: string;
  entity_type: string;
  entity_id: string;
  action_type: string;
};

type DashboardSummary = {
  kpis: {
    total_spend: number;
    avg_cpl: number | null;
    avg_ctr: number;
    total_conversions: number;
    avg_frequency: number;
    campaign_count: number;
  };
  best_campaigns: CampaignRankingItem[];
  critical_campaigns: CampaignRankingItem[];
  top_alerts: Alert[];
};

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border p-5 flex items-start justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-foreground/50">{label}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className="p-2 rounded-md bg-primary/10 text-primary">{icon}</div>
    </div>
  );
}

function HealthBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    excelente: "bg-emerald-500/15 text-emerald-400",
    buena: "bg-primary/15 text-primary",
    atencion: "bg-amber-500/15 text-amber-400",
    critica: "bg-danger/15 text-danger",
  };
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${colors[status] ?? ""}`}>{status}</span>
  );
}

export default function DashboardHome() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [noAccount, setNoAccount] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const accounts = await apiFetch("/api/v1/ad-accounts");
        if (accounts.length === 0) {
          setNoAccount(true);
          return;
        }
        const data = await apiFetch(`/api/v1/ad-accounts/${accounts[0].id}/dashboard-summary`);
        setSummary(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "No se pudo cargar el resumen");
      }
    })();
  }, []);

  if (noAccount) {
    return (
      <div>
        <h1 className="text-2xl font-semibold mb-2">Aún no tienes cuentas conectadas</h1>
        <p className="text-sm text-foreground/60 mb-4">
          Conecta tu cuenta de Meta Ads para empezar a ver diagnósticos y recomendaciones.
        </p>
        <Link href="/settings/integrations" className="text-sm font-medium text-primary">
          Ir a Integraciones →
        </Link>
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-danger">{error}</p>;
  }

  if (!summary) {
    return <p className="text-sm text-foreground/60">Cargando resumen...</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-1">Resumen general</h1>
      <p className="text-sm text-foreground/60 mb-6">Esto es lo que está pasando hoy en tus campañas.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={<DollarSign size={18} />} label="Gasto total" value={`$${summary.kpis.total_spend}`} />
        <StatCard
          icon={<Target size={18} />}
          label="CPL promedio"
          value={summary.kpis.avg_cpl !== null ? `$${summary.kpis.avg_cpl}` : "—"}
        />
        <StatCard icon={<MousePointerClick size={18} />} label="CTR promedio" value={`${summary.kpis.avg_ctr}%`} />
        <StatCard icon={<AlertTriangle size={18} />} label="Conversiones" value={summary.kpis.total_conversions} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm font-semibold uppercase text-foreground/50 mb-3">Mejores campañas</h2>
          <div className="rounded-lg border border-border divide-y divide-border">
            {summary.best_campaigns.length === 0 && (
              <p className="p-4 text-sm text-foreground/60">Aún no hay campañas con puntaje calculado.</p>
            )}
            {summary.best_campaigns.map((c) => (
              <Link
                key={c.campaign_id}
                href={`/campaigns/${c.campaign_id}`}
                className="flex items-center justify-between p-4 hover:bg-muted"
              >
                <span className="text-sm">{c.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{c.score}</span>
                  <HealthBadge status={c.health_status} />
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase text-foreground/50 mb-3">Campañas críticas</h2>
          <div className="rounded-lg border border-border divide-y divide-border">
            {summary.critical_campaigns.length === 0 && (
              <p className="p-4 text-sm text-foreground/60">Ninguna campaña necesita atención urgente.</p>
            )}
            {summary.critical_campaigns.map((c) => (
              <Link
                key={c.campaign_id}
                href={`/campaigns/${c.campaign_id}`}
                className="flex items-center justify-between p-4 hover:bg-muted"
              >
                <span className="text-sm">{c.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{c.score}</span>
                  <HealthBadge status={c.health_status} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-sm font-semibold uppercase text-foreground/50 mb-3">Recomendaciones IA</h2>
        <div className="rounded-lg border border-border divide-y divide-border">
          {summary.top_alerts.length === 0 && (
            <p className="p-4 text-sm text-foreground/60">No hay recomendaciones pendientes.</p>
          )}
          {summary.top_alerts.map((alert) => (
            <div key={alert.id} className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-medium">{alert.title}</p>
                <p className="text-xs text-foreground/50">{alert.action_type}</p>
              </div>
              <span className="text-xs font-semibold uppercase text-foreground/50">{alert.priority}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
