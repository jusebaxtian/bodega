"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type AdAccount = {
  id: string;
  meta_account_id: string;
  name: string;
  status: string;
};

export default function IntegrationsPage() {
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const loadAccounts = useCallback(async () => {
    const data = await apiFetch("/api/v1/ad-accounts");
    setAccounts(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  const connectMeta = async () => {
    setConnecting(true);
    const { url } = await apiFetch("/api/v1/meta/oauth-url");
    window.location.href = url;
  };

  const syncAccount = async (id: string) => {
    setSyncingId(id);
    await apiFetch(`/api/v1/ad-accounts/${id}/sync`, { method: "POST" });
    setSyncingId(null);
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-1">Integraciones</h1>
      <p className="text-sm text-foreground/60 mb-6">
        Conecta tu cuenta de Meta Ads. AdsControl IA solo lee tus datos — nunca modifica
        campañas, presupuestos ni anuncios en Meta.
      </p>

      <button
        onClick={connectMeta}
        disabled={connecting}
        className="mb-8 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {connecting ? "Redirigiendo..." : "Conectar cuenta de Meta Ads"}
      </button>

      <div className="rounded-lg border border-border">
        {loading ? (
          <p className="p-4 text-sm text-foreground/60">Cargando...</p>
        ) : accounts.length === 0 ? (
          <p className="p-4 text-sm text-foreground/60">Aún no has conectado ninguna cuenta.</p>
        ) : (
          accounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between border-b border-border p-4 last:border-b-0"
            >
              <div>
                <p className="text-sm font-medium">{account.name}</p>
                <p className="text-xs text-foreground/60">{account.meta_account_id}</p>
              </div>
              <button
                onClick={() => syncAccount(account.id)}
                disabled={syncingId === account.id}
                className="rounded-md border border-border px-3 py-1.5 text-xs font-medium disabled:opacity-60"
              >
                {syncingId === account.id ? "Sincronizando..." : "Sincronizar ahora"}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
