import { useState, useEffect, useCallback } from "react";
import {
  Package, Users, LayoutDashboard, LogOut, Plus, Pencil, Trash2, Search,
  AlertTriangle, Eye, EyeOff, Lock, User as UserIcon, Boxes, X, DollarSign,
  TrendingDown, Store, ChevronRight, Check
} from "lucide-react";
import { supabase, usernameToEmail } from "./supabaseClient";

/* ---------------------------------------------------------
   Tokens & helpers
--------------------------------------------------------- */
const ROLE_LABEL = { admin: "Administrador", vendedor: "Vendedor", cliente: "Cliente" };
const ROLE_BADGE = {
  admin: { bg: "#146356", fg: "#FFFFFF" },
  vendedor: { bg: "#D98F3B", fg: "#2B1B05" },
  cliente: { bg: "#E7E4DA", fg: "#3C463F" },
};
const LOW_STOCK = 5;

const cop = (n) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(n || 0);

const pts = (n) => `${new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 }).format(n || 0)} pts`;

const MOVEMENT_LABEL = { recarga: "Recarga", ajuste: "Ajuste", compra: "Compra", redencion: "Redención" };
const REQUEST_STATUS_LABEL = { pendiente: "Pendiente", confirmado: "Confirmado", rechazado: "Rechazado" };

/* ---------------------------------------------------------
   Small UI primitives
--------------------------------------------------------- */
function Toast({ toast }) {
  if (!toast) return null;
  const isErr = toast.type === "error";
  return (
    <div
      className="fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 text-sm font-medium"
      style={{ background: isErr ? "#C4453B" : "#146356", color: "#fff" }}
    >
      {isErr ? <AlertTriangle size={16} /> : <Check size={16} />}
      {toast.message}
    </div>
  );
}

function Badge({ role }) {
  const c = ROLE_BADGE[role] || ROLE_BADGE.cliente;
  return (
    <span className="px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide" style={{ background: c.bg, color: c.fg }}>
      {ROLE_LABEL[role] || role}
    </span>
  );
}

function StatCard({ icon, label, value, accent }) {
  return (
    <div className="rounded-2xl p-5 flex items-start justify-between" style={{ background: "#FFFFFF", border: "1px solid #E1E0D9" }}>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#66756F" }}>{label}</p>
        <p className="font-display text-3xl mt-1" style={{ color: "#1E2A28" }}>{value}</p>
      </div>
      <div className="p-2.5 rounded-xl" style={{ background: accent + "1A" }}>{icon}</div>
    </div>
  );
}

/* ---------------------------------------------------------
   Auth screen (login / register)
--------------------------------------------------------- */
function AuthScreen({ onAuthed, toastFn }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) return toastFn("Completa usuario y contraseña", "error");
    setBusy(true);
    const email = usernameToEmail(username);
    try {
      if (mode === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) toastFn("Usuario o contraseña incorrectos", "error");
        else onAuthed();
      } else {
        if (!name.trim()) { toastFn("Escribe tu nombre", "error"); return; }
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { username: username.trim(), name: name.trim() } },
        });
        if (error) {
          toastFn(error.message.includes("already") ? "Ese usuario ya existe" : error.message, "error");
        } else if (!data.session) {
          toastFn("Cuenta creada. Si tu proyecto pide confirmar el correo, desactívalo en Supabase → Authentication.", "error");
        } else {
          onAuthed();
        }
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex" style={{ background: "#F6F5F1" }}>
      <div className="hidden md:flex md:w-2/5 relative overflow-hidden flex-col justify-between p-10" style={{ background: "#146356" }}>
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg" style={{ background: "#0D4238" }}><Store size={20} color="#F6F5F1" /></div>
          <span className="font-display text-xl" style={{ color: "#F6F5F1" }}>Bodega</span>
        </div>
        <div>
          <p className="font-display text-4xl leading-tight" style={{ color: "#F6F5F1" }}>El control de tu tienda, en un solo lugar.</p>
          <p className="mt-4 text-sm" style={{ color: "#CFE3DC" }}>Usuarios, roles y productos organizados para que tú y tu equipo trabajen sin enredos.</p>
        </div>
        <svg viewBox="0 0 320 140" className="w-full opacity-90" aria-hidden="true">
          <g>
            <rect x="20" y="70" width="60" height="50" rx="4" fill="#0D4238" />
            <rect x="90" y="50" width="60" height="70" rx="4" fill="#1B7A67" />
            <rect x="160" y="80" width="60" height="40" rx="4" fill="#0D4238" />
            <rect x="230" y="40" width="60" height="80" rx="4" fill="#D98F3B" />
          </g>
        </svg>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="md:hidden flex items-center gap-2 mb-8 justify-center">
            <Store size={22} color="#146356" /><span className="font-display text-2xl" style={{ color: "#1E2A28" }}>Bodega</span>
          </div>
          <h1 className="font-display text-2xl mb-1" style={{ color: "#1E2A28" }}>{mode === "login" ? "Inicia sesión" : "Crea tu cuenta"}</h1>
          <p className="text-sm mb-6" style={{ color: "#66756F" }}>{mode === "login" ? "Accede con tu usuario y contraseña." : "Las cuentas nuevas se crean con rol Cliente."}</p>

          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="text-xs font-semibold uppercase tracking-wide" style={{ color: "#66756F" }}>Nombre</label>
                <div className="mt-1 flex items-center gap-2 rounded-lg px-3 py-2.5" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
                  <UserIcon size={16} color="#66756F" />
                  <input value={name} onChange={(e) => setName(e.target.value)} className="w-full outline-none text-sm bg-transparent" placeholder="Tu nombre completo" />
                </div>
              </div>
            )}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide" style={{ color: "#66756F" }}>Usuario</label>
              <div className="mt-1 flex items-center gap-2 rounded-lg px-3 py-2.5" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
                <UserIcon size={16} color="#66756F" />
                <input value={username} onChange={(e) => setUsername(e.target.value)} className="w-full outline-none text-sm bg-transparent" placeholder="ej. admin" autoCapitalize="none" />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide" style={{ color: "#66756F" }}>Contraseña</label>
              <div className="mt-1 flex items-center gap-2 rounded-lg px-3 py-2.5" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
                <Lock size={16} color="#66756F" />
                <input type={showPw ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} className="w-full outline-none text-sm bg-transparent" placeholder="••••••••" />
                <button type="button" onClick={() => setShowPw((s) => !s)}>{showPw ? <EyeOff size={16} color="#66756F" /> : <Eye size={16} color="#66756F" />}</button>
              </div>
            </div>
            <button type="submit" disabled={busy} className="w-full py-2.5 rounded-lg text-sm font-semibold disabled:opacity-60" style={{ background: "#146356", color: "#fff" }}>
              {busy ? "Un momento..." : mode === "login" ? "Entrar" : "Crear cuenta"}
            </button>
          </form>

          <p className="text-sm text-center mt-6" style={{ color: "#66756F" }}>
            {mode === "login" ? "¿No tienes cuenta? " : "¿Ya tienes cuenta? "}
            <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setPassword(""); }} className="font-semibold" style={{ color: "#146356" }}>
              {mode === "login" ? "Regístrate" : "Inicia sesión"}
            </button>
          </p>

          <div className="mt-8 p-3 rounded-lg text-xs leading-relaxed" style={{ background: "#EFEDE4", color: "#66756F" }}>
            <strong style={{ color: "#1E2A28" }}>Primer uso:</strong> regístrate normalmente (quedas como Cliente), y luego sube tu propio rol a Administrador desde la tabla <code className="font-mono">profiles</code> en Supabase.
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------
   Product modal
--------------------------------------------------------- */
function ProductModal({ initial, onClose, onSave }) {
  const [form, setForm] = useState(initial || { name: "", sku: "", category: "", price: "", stock: "", description: "" });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const submit = (e) => {
    e.preventDefault();
    if (!form.name.trim() || form.price === "" || form.stock === "") return;
    onSave({ ...form, price: Number(form.price), stock: Number(form.stock) });
  };
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: "#1E2A2899" }}>
      <div className="w-full max-w-md rounded-2xl p-6" style={{ background: "#fff" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl" style={{ color: "#1E2A28" }}>{initial ? "Editar producto" : "Nuevo producto"}</h3>
          <button onClick={onClose}><X size={18} color="#66756F" /></button>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Nombre</label>
            <input required value={form.name} onChange={(e) => set("name", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold" style={{ color: "#66756F" }}>SKU</label>
              <input value={form.sku} onChange={(e) => set("sku", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none font-mono" style={{ border: "1px solid #E1E0D9" }} />
            </div>
            <div>
              <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Categoría</label>
              <input value={form.category} onChange={(e) => set("category", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Precio (COP)</label>
              <input required type="number" min="0" value={form.price} onChange={(e) => set("price", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
            </div>
            <div>
              <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Stock</label>
              <input required type="number" min="0" value={form.stock} onChange={(e) => set("stock", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Descripción</label>
            <textarea value={form.description} onChange={(e) => set("description", e.target.value)} rows={2} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none resize-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}>Cancelar</button>
            <button type="submit" className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>Guardar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------
   User role modal (admin can only change role — deleting
   auth accounts requires a server-side key we intentionally
   never expose in the browser)
--------------------------------------------------------- */
function UserRoleModal({ initial, onClose, onSave }) {
  const [role, setRole] = useState(initial.role);
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: "#1E2A2899" }}>
      <div className="w-full max-w-sm rounded-2xl p-6" style={{ background: "#fff" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl" style={{ color: "#1E2A28" }}>Editar rol</h3>
          <button onClick={onClose}><X size={18} color="#66756F" /></button>
        </div>
        <p className="text-sm mb-3" style={{ color: "#66756F" }}>{initial.name} · <span className="font-mono">{initial.username}</span></p>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full rounded-lg px-3 py-2 text-sm outline-none mb-4" style={{ border: "1px solid #E1E0D9" }}>
          <option value="admin">Administrador</option>
          <option value="vendedor">Vendedor</option>
          <option value="cliente">Cliente</option>
        </select>
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}>Cancelar</button>
          <button onClick={() => onSave(role)} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>Guardar</button>
        </div>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------
   Points system modals
--------------------------------------------------------- */
function AdjustPointsModal({ initial, onClose, onSave }) {
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const submit = (e) => {
    e.preventDefault();
    if (!amount || Number(amount) === 0) return;
    onSave(Number(amount), note);
  };
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: "#1E2A2899" }}>
      <div className="w-full max-w-sm rounded-2xl p-6" style={{ background: "#fff" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl" style={{ color: "#1E2A28" }}>Ajustar puntos</h3>
          <button onClick={onClose}><X size={18} color="#66756F" /></button>
        </div>
        <p className="text-sm mb-3" style={{ color: "#66756F" }}>{initial.name} · saldo actual: {pts(initial.points_balance)}</p>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Cantidad (usa negativo para quitar)</label>
            <input required type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="ej. 50 o -20" className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Nota (opcional)</label>
            <input value={note} onChange={(e) => setNote(e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}>Cancelar</button>
            <button type="submit" className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>Guardar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DigitalProductModal({ initial, onClose, onSave }) {
  const [form, setForm] = useState(initial || { title: "", description: "", image_url: "", points_price: "", active: true });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const submit = (e) => {
    e.preventDefault();
    if (!form.title.trim() || form.points_price === "") return;
    onSave({ ...form, points_price: Number(form.points_price) });
  };
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: "#1E2A2899" }}>
      <div className="w-full max-w-md rounded-2xl p-6" style={{ background: "#fff" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl" style={{ color: "#1E2A28" }}>{initial ? "Editar producto digital" : "Nuevo producto digital"}</h3>
          <button onClick={onClose}><X size={18} color="#66756F" /></button>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Título</label>
            <input required value={form.title} onChange={(e) => set("title", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>URL de imagen</label>
            <input value={form.image_url} onChange={(e) => set("image_url", e.target.value)} placeholder="https://…" className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Descripción</label>
            <textarea value={form.description} onChange={(e) => set("description", e.target.value)} rows={2} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none resize-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Valor en puntos</label>
              <input required type="number" min="0" step="0.01" value={form.points_price} onChange={(e) => set("points_price", e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
            </div>
            <div className="flex items-end pb-2.5">
              <label className="flex items-center gap-2 text-sm font-medium" style={{ color: "#1E2A28" }}>
                <input type="checkbox" checked={form.active} onChange={(e) => set("active", e.target.checked)} /> Activo
              </label>
            </div>
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}>Cancelar</button>
            <button type="submit" className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>Guardar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function BuyPointsModal({ paymentInfo, onClose, onSave }) {
  const [amount, setAmount] = useState("");
  const [reference, setReference] = useState("");
  const submit = (e) => {
    e.preventDefault();
    if (!amount || Number(amount) <= 0) return;
    onSave(Number(amount), reference);
  };
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: "#1E2A2899" }}>
      <div className="w-full max-w-sm rounded-2xl p-6" style={{ background: "#fff" }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl" style={{ color: "#1E2A28" }}>Comprar puntos</h3>
          <button onClick={onClose}><X size={18} color="#66756F" /></button>
        </div>
        <div className="mb-4 p-3 rounded-lg text-xs leading-relaxed whitespace-pre-wrap" style={{ background: "#EFEDE4", color: "#66756F" }}>{paymentInfo}</div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Puntos a comprar (1 punto = 1 USD)</label>
            <input required type="number" min="1" step="1" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div>
            <label className="text-xs font-semibold" style={{ color: "#66756F" }}>Referencia de la transferencia</label>
            <input value={reference} onChange={(e) => setReference(e.target.value)} placeholder="ej. últimos dígitos, hora, comprobante" className="w-full mt-1 rounded-lg px-3 py-2 text-sm outline-none" style={{ border: "1px solid #E1E0D9" }} />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}>Cancelar</button>
            <button type="submit" className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>Enviar solicitud</button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------
   Main app
--------------------------------------------------------- */
export default function App() {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [products, setProducts] = useState([]);
  const [tab, setTab] = useState("dashboard");
  const [toast, setToast] = useState(null);
  const [search, setSearch] = useState("");
  const [productModal, setProductModal] = useState(null);
  const [roleModal, setRoleModal] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [pointMovements, setPointMovements] = useState([]);
  const [digitalProducts, setDigitalProducts] = useState([]);
  const [purchaseRequests, setPurchaseRequests] = useState([]);
  const [appSettings, setAppSettings] = useState({});
  const [adjustPointsModal, setAdjustPointsModal] = useState(null);
  const [digitalProductModal, setDigitalProductModal] = useState(null);
  const [buyPointsModal, setBuyPointsModal] = useState(false);
  const [brebeInfoDraft, setBrebeInfoDraft] = useState("");

  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 2600);
  };

  const loadProfile = useCallback(async (userId) => {
    const { data, error } = await supabase.from("profiles").select("*").eq("id", userId).single();
    if (!error) setProfile(data);
  }, []);

  const loadProducts = useCallback(async () => {
    const { data, error } = await supabase.from("products").select("*").order("created_at", { ascending: false });
    if (!error) setProducts(data || []);
  }, []);

  const loadProfiles = useCallback(async () => {
    const { data, error } = await supabase.from("profiles").select("*").order("created_at", { ascending: true });
    if (!error) setProfiles(data || []);
  }, []);

  const loadDigitalProducts = useCallback(async () => {
    const { data, error } = await supabase.from("digital_products").select("*").order("created_at", { ascending: false });
    if (!error) setDigitalProducts(data || []);
  }, []);

  const loadAppSettings = useCallback(async () => {
    const { data, error } = await supabase.from("app_settings").select("*");
    if (!error) {
      const map = {};
      (data || []).forEach((s) => { map[s.key] = s.value; });
      setAppSettings(map);
      setBrebeInfoDraft(map.brebe_info || "");
    }
  }, []);

  const loadPointMovements = useCallback(async (userId, isAdmin) => {
    let query = supabase.from("point_movements").select("*").order("created_at", { ascending: false });
    if (!isAdmin) query = query.eq("profile_id", userId);
    const { data, error } = await query;
    if (!error) setPointMovements(data || []);
  }, []);

  const loadPurchaseRequests = useCallback(async (userId, isAdmin) => {
    let query = supabase.from("point_purchase_requests").select("*").order("created_at", { ascending: false });
    if (!isAdmin) query = query.eq("profile_id", userId);
    const { data, error } = await query;
    if (!error) setPurchaseRequests(data || []);
  }, []);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => setSession(s));
    return () => sub.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (session?.user) {
      loadProfile(session.user.id);
      loadProducts();
      loadDigitalProducts();
      loadAppSettings();
    } else {
      setProfile(null);
    }
  }, [session, loadProfile, loadProducts, loadDigitalProducts, loadAppSettings]);

  useEffect(() => {
    if (profile?.role === "admin") loadProfiles();
  }, [profile, loadProfiles]);

  useEffect(() => {
    if (profile) {
      loadPointMovements(profile.id, profile.role === "admin");
      loadPurchaseRequests(profile.id, profile.role === "admin");
    }
  }, [profile, loadPointMovements, loadPurchaseRequests]);

  const logout = async () => { await supabase.auth.signOut(); setTab("dashboard"); };

  const role = profile?.role;
  const canManageProducts = role === "admin" || role === "vendedor";
  const canManageUsers = role === "admin";

  const filteredProducts = products.filter((p) => (p.name + (p.sku || "") + (p.category || "")).toLowerCase().includes(search.toLowerCase()));
  const stockValue = products.reduce((s, p) => s + p.price * p.stock, 0);
  const lowStock = products.filter((p) => p.stock < LOW_STOCK);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center" style={{ background: "#F6F5F1" }}><p className="text-sm" style={{ color: "#66756F" }}>Cargando Bodega…</p></div>;
  }

  if (!session || !profile) {
    return (
      <>
        <style>{FONT_STYLE}</style>
        <Toast toast={toast} />
        <AuthScreen onAuthed={() => {}} toastFn={showToast} />
      </>
    );
  }

  const redeemedTotal = pointMovements.filter((m) => m.type === "redencion").reduce((s, m) => s + Math.abs(m.amount), 0);
  const activeDigitalProducts = digitalProducts.filter((p) => p.active);
  const pendingRequests = purchaseRequests.filter((r) => r.status === "pendiente");

  const NAV = [
    { key: "dashboard", label: "Panel", icon: LayoutDashboard, show: true },
    { key: "products", label: role === "cliente" ? "Catálogo" : "Productos", icon: Package, show: true },
    { key: "users", label: "User", icon: Users, show: canManageUsers },
    { key: "points", label: "Puntos", icon: DollarSign, show: canManageUsers },
    { key: "digital", label: "Tienda digital", icon: Boxes, show: canManageUsers },
    { key: "mypoints", label: "Mis puntos", icon: DollarSign, show: role === "cliente" },
    { key: "store", label: "Canjear", icon: Boxes, show: role === "cliente" },
  ];

  return (
    <div className="min-h-screen flex" style={{ background: "#F6F5F1" }}>
      <style>{FONT_STYLE}</style>
      <Toast toast={toast} />

      <aside className="w-60 shrink-0 hidden sm:flex flex-col p-5" style={{ background: "#fff", borderRight: "1px solid #E1E0D9" }}>
        <div className="flex items-center gap-2 mb-8">
          <div className="p-1.5 rounded-lg" style={{ background: "#146356" }}><Store size={16} color="#fff" /></div>
          <span className="font-display text-lg" style={{ color: "#1E2A28" }}>Bodega</span>
        </div>
        <nav className="space-y-1 flex-1">
          {NAV.filter((n) => n.show).map((n) => (
            <button key={n.key} onClick={() => setTab(n.key)} className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium"
              style={tab === n.key ? { background: "#146356", color: "#fff" } : { color: "#1E2A28" }}>
              <n.icon size={16} />{n.label}{tab === n.key && <ChevronRight size={14} className="ml-auto" />}
            </button>
          ))}
        </nav>
        <div className="pt-4" style={{ borderTop: "1px solid #E1E0D9" }}>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style={{ background: "#EFEDE4", color: "#1E2A28" }}>
              {profile.name.slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate" style={{ color: "#1E2A28" }}>{profile.name}</p>
              <Badge role={role} />
            </div>
          </div>
          <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium" style={{ color: "#C4453B" }}>
            <LogOut size={15} /> Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="flex-1 p-5 sm:p-8 overflow-y-auto">
        <div className="sm:hidden flex items-center justify-between mb-6">
          <div className="flex items-center gap-2"><Store size={18} color="#146356" /><span className="font-display text-lg" style={{ color: "#1E2A28" }}>Bodega</span></div>
          <button onClick={logout}><LogOut size={16} color="#C4453B" /></button>
        </div>
        <div className="sm:hidden flex gap-2 mb-6 overflow-x-auto">
          {NAV.filter((n) => n.show).map((n) => (
            <button key={n.key} onClick={() => setTab(n.key)} className="px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap"
              style={tab === n.key ? { background: "#146356", color: "#fff" } : { background: "#EFEDE4", color: "#1E2A28" }}>{n.label}</button>
          ))}
        </div>

        {tab === "dashboard" && (
          <div>
            <h1 className="font-display text-3xl mb-1" style={{ color: "#1E2A28" }}>Hola, {profile.name.split(" ")[0]}</h1>
            <p className="text-sm mb-6" style={{ color: "#66756F" }}>Esto es lo que pasa hoy en tu bodega.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <StatCard icon={<Boxes size={20} color="#146356" />} accent="#146356" label="Productos" value={products.length} />
              <StatCard icon={<DollarSign size={20} color="#D98F3B" />} accent="#D98F3B" label="Valor de inventario" value={cop(stockValue)} />
              <StatCard icon={<TrendingDown size={20} color="#C4453B" />} accent="#C4453B" label="Stock bajo" value={lowStock.length} />
              {canManageUsers && <StatCard icon={<Users size={20} color="#3D8361" />} accent="#3D8361" label="Usuarios" value={profiles.length} />}
            </div>
            {lowStock.length > 0 && canManageProducts && (
              <div className="mt-8">
                <h2 className="font-display text-lg mb-3" style={{ color: "#1E2A28" }}>Necesitan reabastecerse</h2>
                <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
                  {lowStock.map((p) => (
                    <div key={p.id} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid #F0EFE9" }}>
                      <div><p className="text-sm font-medium" style={{ color: "#1E2A28" }}>{p.name}</p><p className="text-xs font-mono" style={{ color: "#66756F" }}>{p.sku || "sin SKU"}</p></div>
                      <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: "#C4453B1A", color: "#C4453B" }}>{p.stock} unid.</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "products" && (
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              <div>
                <h1 className="font-display text-3xl" style={{ color: "#1E2A28" }}>{role === "cliente" ? "Catálogo" : "Productos"}</h1>
                <p className="text-sm" style={{ color: "#66756F" }}>{filteredProducts.length} producto(s)</p>
              </div>
              <div className="flex gap-2">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
                  <Search size={15} color="#66756F" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar…" className="outline-none text-sm bg-transparent w-40" />
                </div>
                {canManageProducts && (
                  <button onClick={() => setProductModal({ mode: "new" })} className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>
                    <Plus size={15} /> Nuevo
                  </button>
                )}
              </div>
            </div>

            {role === "cliente" ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredProducts.map((p) => (
                  <div key={p.id} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #E1E0D9" }}>
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: "#EFEDE4", color: "#66756F" }}>{p.category || "General"}</span>
                      {p.stock < LOW_STOCK && p.stock > 0 && <span className="text-xs font-bold" style={{ color: "#D98F3B" }}>Pocas unidades</span>}
                      {p.stock === 0 && <span className="text-xs font-bold" style={{ color: "#C4453B" }}>Agotado</span>}
                    </div>
                    <p className="font-display text-lg" style={{ color: "#1E2A28" }}>{p.name}</p>
                    <p className="text-sm mt-1" style={{ color: "#66756F" }}>{p.description}</p>
                    <p className="font-display text-2xl mt-3" style={{ color: "#146356" }}>{cop(p.price)}</p>
                  </div>
                ))}
                {filteredProducts.length === 0 && <p className="text-sm" style={{ color: "#66756F" }}>No hay productos que coincidan con tu búsqueda.</p>}
              </div>
            ) : (
              <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ background: "#F6F5F1" }}>
                      <th className="text-left px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Producto</th>
                      <th className="text-left px-4 py-3 font-semibold hidden md:table-cell" style={{ color: "#66756F" }}>SKU</th>
                      <th className="text-left px-4 py-3 font-semibold hidden md:table-cell" style={{ color: "#66756F" }}>Categoría</th>
                      <th className="text-right px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Precio</th>
                      <th className="text-right px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Stock</th>
                      <th className="text-right px-4 py-3 font-semibold" style={{ color: "#66756F" }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredProducts.map((p) => (
                      <tr key={p.id} style={{ borderTop: "1px solid #F0EFE9" }}>
                        <td className="px-4 py-3 font-medium" style={{ color: "#1E2A28" }}>{p.name}</td>
                        <td className="px-4 py-3 font-mono text-xs hidden md:table-cell" style={{ color: "#66756F" }}>{p.sku}</td>
                        <td className="px-4 py-3 hidden md:table-cell" style={{ color: "#66756F" }}>{p.category}</td>
                        <td className="px-4 py-3 text-right" style={{ color: "#1E2A28" }}>{cop(p.price)}</td>
                        <td className="px-4 py-3 text-right"><span className="font-semibold" style={{ color: p.stock < LOW_STOCK ? "#C4453B" : "#1E2A28" }}>{p.stock}</span></td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <button onClick={() => setProductModal({ mode: "edit", data: p })} className="p-1.5 rounded-lg hover:opacity-70"><Pencil size={14} color="#66756F" /></button>
                            <button onClick={() => setConfirmDelete({ type: "product", id: p.id, label: p.name })} className="p-1.5 rounded-lg hover:opacity-70"><Trash2 size={14} color="#C4453B" /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredProducts.length === 0 && <p className="text-sm p-4" style={{ color: "#66756F" }}>No hay productos que coincidan.</p>}
              </div>
            )}
          </div>
        )}

        {tab === "users" && canManageUsers && (
          <div>
            <div className="mb-6">
              <h1 className="font-display text-3xl" style={{ color: "#1E2A28" }}>Usuarios</h1>
              <p className="text-sm" style={{ color: "#66756F" }}>{profiles.length} cuenta(s) · las cuentas nuevas se crean desde la pantalla de registro</p>
            </div>
            <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: "#F6F5F1" }}>
                    <th className="text-left px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Nombre</th>
                    <th className="text-left px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Usuario</th>
                    <th className="text-left px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Rol</th>
                    <th className="text-right px-4 py-3 font-semibold" style={{ color: "#66756F" }}></th>
                  </tr>
                </thead>
                <tbody>
                  {profiles.map((u) => (
                    <tr key={u.id} style={{ borderTop: "1px solid #F0EFE9" }}>
                      <td className="px-4 py-3 font-medium" style={{ color: "#1E2A28" }}>{u.name} {u.id === profile.id && <span style={{ color: "#66756F" }}>(tú)</span>}</td>
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: "#66756F" }}>{u.username}</td>
                      <td className="px-4 py-3"><Badge role={u.role} /></td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => setRoleModal(u)} className="p-1.5 rounded-lg hover:opacity-70"><Pencil size={14} color="#66756F" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "points" && canManageUsers && (
          <div>
            <div className="mb-6">
              <h1 className="font-display text-3xl" style={{ color: "#1E2A28" }}>Puntos</h1>
              <p className="text-sm" style={{ color: "#66756F" }}>Recarga, quita y revisa el saldo de puntos de tus clientes.</p>
            </div>

            <div className="rounded-2xl overflow-hidden mb-8" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: "#F6F5F1" }}>
                    <th className="text-left px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Cliente</th>
                    <th className="text-left px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Usuario</th>
                    <th className="text-right px-4 py-3 font-semibold" style={{ color: "#66756F" }}>Saldo</th>
                    <th className="text-right px-4 py-3 font-semibold" style={{ color: "#66756F" }}></th>
                  </tr>
                </thead>
                <tbody>
                  {profiles.filter((u) => u.role === "cliente").map((u) => (
                    <tr key={u.id} style={{ borderTop: "1px solid #F0EFE9" }}>
                      <td className="px-4 py-3 font-medium" style={{ color: "#1E2A28" }}>{u.name}</td>
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: "#66756F" }}>{u.username}</td>
                      <td className="px-4 py-3 text-right font-semibold" style={{ color: "#1E2A28" }}>{pts(u.points_balance)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => setAdjustPointsModal(u)} className="px-3 py-1.5 rounded-lg text-xs font-semibold" style={{ background: "#146356", color: "#fff" }}>Ajustar</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {profiles.filter((u) => u.role === "cliente").length === 0 && (
                    <tr><td colSpan={4} className="px-4 py-4 text-sm" style={{ color: "#66756F" }}>Aún no hay clientes registrados.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <h2 className="font-display text-lg mb-3" style={{ color: "#1E2A28" }}>Solicitudes de compra pendientes</h2>
            <div className="rounded-2xl overflow-hidden mb-8" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
              {pendingRequests.length === 0 ? (
                <p className="text-sm p-4" style={{ color: "#66756F" }}>No hay solicitudes pendientes.</p>
              ) : (
                pendingRequests.map((r) => {
                  const clientProfile = profiles.find((p) => p.id === r.profile_id);
                  return (
                    <div key={r.id} className="flex items-center justify-between px-4 py-3 gap-3" style={{ borderBottom: "1px solid #F0EFE9" }}>
                      <div>
                        <p className="text-sm font-medium" style={{ color: "#1E2A28" }}>{clientProfile?.name || "Cliente"} · {pts(r.points_requested)}</p>
                        <p className="text-xs" style={{ color: "#66756F" }}>Ref: {r.reference || "sin referencia"}</p>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button
                          onClick={async () => {
                            const { error } = await supabase.rpc("confirm_point_purchase", { p_request_id: r.id });
                            if (error) showToast(error.message, "error"); else showToast("Compra confirmada, puntos acreditados");
                            await Promise.all([loadPurchaseRequests(profile.id, true), loadProfiles(), loadPointMovements(profile.id, true)]);
                          }}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold" style={{ background: "#146356", color: "#fff" }}
                        >Confirmar</button>
                        <button
                          onClick={async () => {
                            const { error } = await supabase.rpc("reject_point_purchase", { p_request_id: r.id });
                            if (error) showToast(error.message, "error"); else showToast("Solicitud rechazada");
                            await loadPurchaseRequests(profile.id, true);
                          }}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}
                        >Rechazar</button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <h2 className="font-display text-lg mb-3" style={{ color: "#1E2A28" }}>Datos de pago (Bre-B)</h2>
            <div className="rounded-2xl p-5" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
              <textarea value={brebeInfoDraft} onChange={(e) => setBrebeInfoDraft(e.target.value)} rows={3} className="w-full rounded-lg px-3 py-2 text-sm outline-none resize-none" style={{ border: "1px solid #E1E0D9" }} placeholder="Llave Bre-B, nombre de la cuenta, banco…" />
              <button
                onClick={async () => {
                  const { error } = await supabase.from("app_settings").upsert({ key: "brebe_info", value: brebeInfoDraft });
                  if (error) showToast(error.message, "error"); else showToast("Datos de pago actualizados");
                  await loadAppSettings();
                }}
                className="mt-3 px-4 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}
              >Guardar</button>
            </div>
          </div>
        )}

        {tab === "digital" && canManageUsers && (
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              <div>
                <h1 className="font-display text-3xl" style={{ color: "#1E2A28" }}>Tienda digital</h1>
                <p className="text-sm" style={{ color: "#66756F" }}>{digitalProducts.length} producto(s) canjeables por puntos</p>
              </div>
              <button onClick={() => setDigitalProductModal({ mode: "new" })} className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold" style={{ background: "#146356", color: "#fff" }}>
                <Plus size={15} /> Nuevo
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {digitalProducts.map((p) => (
                <div key={p.id} className="rounded-2xl overflow-hidden" style={{ background: "#fff", border: "1px solid #E1E0D9" }}>
                  {p.image_url && <img src={p.image_url} alt={p.title} className="w-full h-32 object-cover" />}
                  <div className="p-5">
                    <div className="flex items-start justify-between mb-2 gap-2">
                      <p className="font-display text-lg" style={{ color: "#1E2A28" }}>{p.title}</p>
                      {!p.active && <span className="text-xs font-bold px-2 py-0.5 rounded-full shrink-0" style={{ background: "#EFEDE4", color: "#66756F" }}>Inactivo</span>}
                    </div>
                    <p className="text-sm mt-1" style={{ color: "#66756F" }}>{p.description}</p>
                    <div className="flex items-center justify-between mt-3">
                      <p className="font-display text-xl" style={{ color: "#146356" }}>{pts(p.points_price)}</p>
                      <div className="flex items-center gap-1">
                        <button onClick={() => setDigitalProductModal({ mode: "edit", data: p })} className="p-1.5 rounded-lg hover:opacity-70"><Pencil size={14} color="#66756F" /></button>
                        <button onClick={() => setConfirmDelete({ type: "digital_product", id: p.id, label: p.title })} className="p-1.5 rounded-lg hover:opacity-70"><Trash2 size={14} color="#C4453B" /></button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {digitalProducts.length === 0 && <p className="text-sm" style={{ color: "#66756F" }}>Aún no has creado productos digitales.</p>}
            </div>
          </div>
        )}

        {tab === "mypoints" && role === "cliente" && (
          <div>
            <h1 className="font-display text-3xl mb-1" style={{ color: "#1E2A28" }}>Mis puntos</h1>
            <p className="text-sm mb-6" style={{ color: "#66756F" }}>1 punto = 1 USD.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <StatCard icon={<DollarSign size={20} color="#146356" />} accent="#146356" label="Saldo actual" value={pts(profile.points_balance)} />
              <StatCard icon={<Boxes size={20} color="#D98F3B" />} accent="#D98F3B" label="Puntos redimidos" value={pts(redeemedTotal)} />
            </div>
            <button onClick={() => setBuyPointsModal(true)} className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold mb-8" style={{ background: "#146356", color: "#fff" }}>
              <Plus size={15} /> Comprar puntos
            </button>

            <h2 className="font-display text-lg mb-3" style={{ color: "#1E2A28" }}>Mis solicitudes de compra</h2>
            <div className="rounded-2xl overflow-hidden mb-8" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
              {purchaseRequests.length === 0 ? (
                <p className="text-sm p-4" style={{ color: "#66756F" }}>Aún no has solicitado comprar puntos.</p>
              ) : (
                purchaseRequests.map((r) => (
                  <div key={r.id} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid #F0EFE9" }}>
                    <div>
                      <p className="text-sm font-medium" style={{ color: "#1E2A28" }}>{pts(r.points_requested)}</p>
                      <p className="text-xs" style={{ color: "#66756F" }}>{new Date(r.created_at).toLocaleString("es-CO")}</p>
                    </div>
                    <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: "#EFEDE4", color: "#1E2A28" }}>{REQUEST_STATUS_LABEL[r.status]}</span>
                  </div>
                ))
              )}
            </div>

            <h2 className="font-display text-lg mb-3" style={{ color: "#1E2A28" }}>Movimientos</h2>
            <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid #E1E0D9", background: "#fff" }}>
              {pointMovements.length === 0 ? (
                <p className="text-sm p-4" style={{ color: "#66756F" }}>Aún no tienes movimientos de puntos.</p>
              ) : (
                pointMovements.map((m) => (
                  <div key={m.id} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid #F0EFE9" }}>
                    <div>
                      <p className="text-sm font-medium" style={{ color: "#1E2A28" }}>{MOVEMENT_LABEL[m.type]}{m.note ? ` · ${m.note}` : ""}</p>
                      <p className="text-xs" style={{ color: "#66756F" }}>{new Date(m.created_at).toLocaleString("es-CO")}</p>
                    </div>
                    <span className="text-sm font-bold" style={{ color: m.amount < 0 ? "#C4453B" : "#3D8361" }}>{m.amount > 0 ? "+" : ""}{pts(m.amount)}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {tab === "store" && role === "cliente" && (
          <div>
            <h1 className="font-display text-3xl mb-1" style={{ color: "#1E2A28" }}>Canjear puntos</h1>
            <p className="text-sm mb-6" style={{ color: "#66756F" }}>Saldo disponible: {pts(profile.points_balance)}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeDigitalProducts.map((p) => {
                const canAfford = profile.points_balance >= p.points_price;
                return (
                  <div key={p.id} className="rounded-2xl overflow-hidden" style={{ background: "#fff", border: "1px solid #E1E0D9" }}>
                    {p.image_url && <img src={p.image_url} alt={p.title} className="w-full h-32 object-cover" />}
                    <div className="p-5">
                      <p className="font-display text-lg" style={{ color: "#1E2A28" }}>{p.title}</p>
                      <p className="text-sm mt-1" style={{ color: "#66756F" }}>{p.description}</p>
                      <div className="flex items-center justify-between mt-3">
                        <p className="font-display text-xl" style={{ color: "#146356" }}>{pts(p.points_price)}</p>
                        <button
                          disabled={!canAfford}
                          onClick={async () => {
                            const { error } = await supabase.rpc("redeem_digital_product", { p_product_id: p.id });
                            if (error) showToast(error.message, "error");
                            else {
                              showToast("Producto canjeado");
                              await Promise.all([loadProfile(profile.id), loadPointMovements(profile.id, false)]);
                            }
                          }}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-50"
                          style={{ background: "#146356", color: "#fff" }}
                        >{canAfford ? "Canjear" : "Puntos insuficientes"}</button>
                      </div>
                    </div>
                  </div>
                );
              })}
              {activeDigitalProducts.length === 0 && <p className="text-sm" style={{ color: "#66756F" }}>Aún no hay productos disponibles para canjear.</p>}
            </div>
          </div>
        )}
      </main>

      {productModal && (
        <ProductModal
          initial={productModal.mode === "edit" ? productModal.data : null}
          onClose={() => setProductModal(null)}
          onSave={async (p) => {
            if (productModal.mode === "edit") {
              const { error } = await supabase.from("products").update(p).eq("id", p.id);
              if (error) showToast(error.message, "error"); else showToast("Producto actualizado");
            } else {
              const { error } = await supabase.from("products").insert(p);
              if (error) showToast(error.message, "error"); else showToast("Producto creado");
            }
            await loadProducts();
            setProductModal(null);
          }}
        />
      )}

      {roleModal && (
        <UserRoleModal
          initial={roleModal}
          onClose={() => setRoleModal(null)}
          onSave={async (role) => {
            const { error } = await supabase.from("profiles").update({ role }).eq("id", roleModal.id);
            if (error) showToast(error.message, "error"); else showToast("Rol actualizado");
            await loadProfiles();
            setRoleModal(null);
          }}
        />
      )}

      {adjustPointsModal && (
        <AdjustPointsModal
          initial={adjustPointsModal}
          onClose={() => setAdjustPointsModal(null)}
          onSave={async (amount, note) => {
            const { error } = await supabase.rpc("admin_adjust_points", {
              p_profile_id: adjustPointsModal.id, p_amount: amount, p_note: note || null,
            });
            if (error) showToast(error.message, "error"); else showToast("Puntos ajustados");
            await Promise.all([loadProfiles(), loadPointMovements(profile.id, true)]);
            setAdjustPointsModal(null);
          }}
        />
      )}

      {digitalProductModal && (
        <DigitalProductModal
          initial={digitalProductModal.mode === "edit" ? digitalProductModal.data : null}
          onClose={() => setDigitalProductModal(null)}
          onSave={async (p) => {
            if (digitalProductModal.mode === "edit") {
              const { error } = await supabase.from("digital_products").update(p).eq("id", p.id);
              if (error) showToast(error.message, "error"); else showToast("Producto digital actualizado");
            } else {
              const { error } = await supabase.from("digital_products").insert(p);
              if (error) showToast(error.message, "error"); else showToast("Producto digital creado");
            }
            await loadDigitalProducts();
            setDigitalProductModal(null);
          }}
        />
      )}

      {buyPointsModal && (
        <BuyPointsModal
          paymentInfo={appSettings.brebe_info || "Contacta al administrador para los datos de pago."}
          onClose={() => setBuyPointsModal(false)}
          onSave={async (amount, reference) => {
            const { error } = await supabase.from("point_purchase_requests").insert({
              profile_id: profile.id, points_requested: amount, reference: reference || null,
            });
            if (error) showToast(error.message, "error"); else showToast("Solicitud enviada, espera la confirmación del admin");
            await loadPurchaseRequests(profile.id, false);
            setBuyPointsModal(false);
          }}
        />
      )}

      {confirmDelete && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4" style={{ background: "#1E2A2899" }}>
          <div className="w-full max-w-sm rounded-2xl p-6" style={{ background: "#fff" }}>
            <div className="flex items-center gap-2 mb-3"><AlertTriangle size={18} color="#C4453B" /><h3 className="font-display text-lg" style={{ color: "#1E2A28" }}>Confirmar eliminación</h3></div>
            <p className="text-sm mb-5" style={{ color: "#66756F" }}>¿Seguro que quieres eliminar <strong style={{ color: "#1E2A28" }}>{confirmDelete.label}</strong>? Esta acción no se puede deshacer.</p>
            <div className="flex gap-2">
              <button onClick={() => setConfirmDelete(null)} className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ border: "1px solid #E1E0D9", color: "#1E2A28" }}>Cancelar</button>
              <button
                onClick={async () => {
                  const table = confirmDelete.type === "digital_product" ? "digital_products" : "products";
                  const { error } = await supabase.from(table).delete().eq("id", confirmDelete.id);
                  if (error) showToast(error.message, "error"); else showToast(confirmDelete.type === "digital_product" ? "Producto digital eliminado" : "Producto eliminado");
                  if (confirmDelete.type === "digital_product") await loadDigitalProducts(); else await loadProducts();
                  setConfirmDelete(null);
                }}
                className="flex-1 py-2 rounded-lg text-sm font-semibold" style={{ background: "#C4453B", color: "#fff" }}
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const FONT_STYLE = `
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.font-display { font-family: 'Fraunces', serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }
button { cursor: pointer; }
input:focus, textarea:focus, select:focus { outline: 2px solid #146356AA; outline-offset: 1px; }
`;
