import { createClient } from "@supabase/supabase-js";

// La URL y la clave "publishable" son seguras para usar en el navegador:
// el acceso real a los datos lo controlan las políticas RLS en Supabase.
const SUPABASE_URL = "https://vuvhfplvwfnpykqmpkmj.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "sb_publishable_ZyVxc9ZErEXAWr3VaSyZ4Q_7fNmntkb";

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);

// Supabase Auth trabaja con "email". Como en Bodega el login es por
// nombre de usuario, generamos un correo interno a partir del username.
export const usernameToEmail = (username) =>
  `${username.trim().toLowerCase().replace(/[^a-z0-9._-]/g, "")}@bodega.internal`;
