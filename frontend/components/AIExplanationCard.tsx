"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

type AIExplanation = {
  main_problem: string;
  severity: "baja" | "media" | "alta" | "critica";
  diagnosis: string;
  immediate_actions: string[];
  actions_72h: string[];
  confidence: number;
  explanation_simple: string;
};

const SEVERITY_COLOR: Record<string, string> = {
  baja: "text-emerald-400",
  media: "text-amber-400",
  alta: "text-orange-400",
  critica: "text-danger",
};

export function AIExplanationCard({ adId }: { adId: string }) {
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch("/api/v1/ai/explain", {
        method: "POST",
        body: JSON.stringify({ entity_type: "ad", entity_id: adId }),
      });
      setExplanation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo generar el diagnóstico");
    } finally {
      setLoading(false);
    }
  };

  if (!explanation) {
    return (
      <div className="rounded-lg border border-border p-5">
        <p className="text-sm text-foreground/60 mb-3">
          Aún no hay un diagnóstico de IA para este anuncio.
        </p>
        <button
          onClick={generate}
          disabled={loading}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? "Analizando..." : "Generar diagnóstico"}
        </button>
        {error && <p className="mt-2 text-sm text-danger">{error}</p>}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{explanation.main_problem}</h3>
        <span className={`text-xs font-semibold uppercase ${SEVERITY_COLOR[explanation.severity]}`}>
          {explanation.severity}
        </span>
      </div>

      <p className="text-sm text-foreground/80">{explanation.diagnosis}</p>

      <div>
        <p className="text-xs font-semibold uppercase text-foreground/50 mb-1">Acciones inmediatas</p>
        <ul className="list-disc list-inside text-sm space-y-0.5">
          {explanation.immediate_actions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase text-foreground/50 mb-1">Próximas 72 horas</p>
        <ul className="list-disc list-inside text-sm space-y-0.5">
          {explanation.actions_72h.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      </div>

      <p className="text-xs text-foreground/50">
        Confianza: {explanation.confidence}% · {explanation.explanation_simple}
      </p>
    </div>
  );
}
