"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

function MetaCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("Meta no devolvió un código de autorización.");
      return;
    }

    (async () => {
      try {
        const me = await apiFetch("/api/v1/me");
        const org = me.orgs[0];
        if (!org) {
          setError("Tu usuario no pertenece a ninguna organización todavía.");
          return;
        }

        await apiFetch("/api/v1/meta/callback", {
          method: "POST",
          body: JSON.stringify({ code, org_id: org.id }),
        });

        router.replace("/settings/integrations");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error conectando con Meta Ads");
      }
    })();
  }, [router, searchParams]);

  return <p className="text-sm text-foreground/60">{error ?? "Conectando tu cuenta de Meta Ads..."}</p>;
}

export default function MetaCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Suspense fallback={<p className="text-sm text-foreground/60">Cargando...</p>}>
        <MetaCallbackContent />
      </Suspense>
    </div>
  );
}
