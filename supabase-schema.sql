-- ============================================================
-- BODEGA — Esquema de base de datos para Supabase
-- Copia y pega TODO este archivo en: Supabase → SQL Editor → New query → Run
-- ============================================================

-- Tabla de perfiles (extiende los usuarios de Supabase Auth con nombre, usuario y rol)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique not null,
  name text not null,
  role text not null default 'cliente' check (role in ('admin','vendedor','cliente')),
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "profiles_select_all" on public.profiles
  for select using (true);

create policy "profiles_insert_own" on public.profiles
  for insert with check (auth.uid() = id);

create policy "profiles_update_own_or_admin" on public.profiles
  for update using (
    auth.uid() = id
    or exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  );

-- Crea automáticamente el perfil (rol "cliente" por defecto) cuando alguien se registra
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, username, name, role)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1)),
    coalesce(new.raw_user_meta_data->>'name', 'Usuario'),
    'cliente'
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Tabla de productos
create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  sku text,
  category text,
  price numeric not null default 0,
  stock integer not null default 0,
  description text,
  created_at timestamptz default now()
);

alter table public.products enable row level security;

-- Cualquier persona con sesión iniciada (Admin, Vendedor o Cliente) puede VER productos
create policy "products_select_all" on public.products
  for select using (true);

-- Solo Admin y Vendedor pueden crear, editar o eliminar productos
create policy "products_write_admin_vendedor" on public.products
  for all using (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('admin','vendedor'))
  )
  with check (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.role in ('admin','vendedor'))
  );

-- ============================================================
-- Después de correr este script:
-- 1. Ve a Authentication → Sign In / Providers → Email y DESACTIVA
--    "Confirm email" (así las cuentas quedan activas al instante).
-- 2. Regístrate en tu app normalmente (quedarás como "cliente").
-- 3. Vuelve aquí al SQL Editor y corre esto para volverte administrador
--    (cambia 'tu_usuario' por el usuario que usaste al registrarte):
--
--    update public.profiles set role = 'admin' where username = 'tu_usuario';
-- ============================================================
