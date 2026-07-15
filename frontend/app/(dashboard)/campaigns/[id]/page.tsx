"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { AIExplanationCard } from "@/components/AIExplanationCard";

type Ad = {
  id: string;
  name: string;
  status: string;
  creative_type: string | null;
  latest_metrics: {
    spend: number;
    ctr: number;
    cpl: number | null;
    frequency: number;
    conversions: number;
  } | null;
};

type AdSet = {
  id: string;
  name: string;
  status: string;
  ads: Ad[];
};

type CampaignDetail = {
  id: string;
  name: string;
  objective: string | null;
  status: string;
  score: number | null;
  health_status: string | null;
  ad_sets: AdSet[];
};

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [selectedAdId, setSelectedAdId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await apiFetch(`/api/v1/campaigns/${params.id}`);
        setCampaign(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "No se pudo cargar la campaña");
      }
    })();
  }, [params.id]);

  if (error) return <p className="text-sm text-danger">{error}</p>;
  if (!campaign) return <p className="text-sm text-foreground/60">Cargando...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-semibold">{campaign.name}</h1>
        {campaign.score !== null && (
          <span className="text-sm font-semibold">
            {campaign.score}/100 · {campaign.health_status}
          </span>
        )}
      </div>
      <p className="text-sm text-foreground/60 mb-6">{campaign.objective ?? "Sin objetivo definido"}</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-sm font-semibold uppercase text-foreground/50 mb-3">Anuncios</h2>
          <div className="rounded-lg border border-border divide-y divide-border">
            {campaign.ad_sets.flatMap((adSet) => adSet.ads).length === 0 && (
              <p className="p-4 text-sm text-foreground/60">Esta campaña aún no tiene anuncios sincronizados.</p>
            )}
            {campaign.ad_sets.map((adSet) =>
              adSet.ads.map((ad) => (
                <button
                  key={ad.id}
                  onClick={() => setSelectedAdId(ad.id)}
                  className={`w-full text-left p-4 hover:bg-muted ${selectedAdId === ad.id ? "bg-muted" : ""}`}
                >
                  <p className="text-sm font-medium">{ad.name}</p>
                  {ad.latest_metrics && (
                    <p className="text-xs text-foreground/50 mt-0.5">
                      CTR {ad.latest_metrics.ctr}% · CPL {ad.latest_metrics.cpl ?? "—"} · Frecuencia{" "}
                      {ad.latest_metrics.frequency}
                    </p>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase text-foreground/50 mb-3">Diagnóstico IA</h2>
          {selectedAdId ? (
            <AIExplanationCard adId={selectedAdId} />
          ) : (
            <p className="text-sm text-foreground/60">Selecciona un anuncio para ver su diagnóstico.</p>
          )}
        </div>
      </div>
    </div>
  );
}
