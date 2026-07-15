import { LayoutDashboard, Megaphone, Settings } from "lucide-react";

const NAV = [
  { label: "Resumen", icon: LayoutDashboard, href: "/" },
  { label: "Campañas", icon: Megaphone, href: "/campaigns" },
  { label: "Configuración", icon: Settings, href: "/settings" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-border p-5 hidden sm:flex flex-col gap-1">
        <div className="mb-6 text-lg font-semibold">AdsControl IA</div>
        {NAV.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-foreground/80 hover:bg-muted"
          >
            <item.icon size={16} />
            {item.label}
          </a>
        ))}
      </aside>
      <main className="flex-1 p-6 sm:p-8">{children}</main>
    </div>
  );
}
