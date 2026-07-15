import { createClient } from "@/lib/supabase/server";

export default async function DashboardHome() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-1">Hola, {user?.email}</h1>
      <p className="text-sm text-foreground/60">
        Este es el placeholder del Módulo 1. El resumen de campañas, KPIs y recomendaciones IA
        llegan en los módulos siguientes (integración con Meta Ads y motor de reglas).
      </p>
    </div>
  );
}
