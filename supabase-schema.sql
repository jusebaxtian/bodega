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
-- Sistema de puntos (1 punto = 1 USD)
-- ============================================================

alter table public.profiles add column if not exists points_balance numeric not null default 0;

-- Movimientos de puntos (historial: recargas, ajustes, compras, redenciones)
create table if not exists public.point_movements (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  amount numeric not null,
  type text not null check (type in ('recarga','ajuste','compra','redencion')),
  note text,
  created_by uuid references public.profiles(id),
  created_at timestamptz default now()
);

alter table public.point_movements enable row level security;

create policy "point_movements_select_own_or_admin" on public.point_movements
  for select using (
    profile_id = auth.uid()
    or exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  );

-- Productos digitales canjeables por puntos
create table if not exists public.digital_products (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  image_url text,
  points_price numeric not null default 0,
  active boolean not null default true,
  created_at timestamptz default now()
);

alter table public.digital_products enable row level security;

create policy "digital_products_select_all" on public.digital_products
  for select using (true);

create policy "digital_products_write_admin" on public.digital_products
  for all using (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  )
  with check (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  );

-- Redenciones de productos digitales
create table if not exists public.redemptions (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  product_id uuid references public.digital_products(id),
  product_title text not null,
  points_spent numeric not null,
  created_at timestamptz default now()
);

alter table public.redemptions enable row level security;

create policy "redemptions_select_own_or_admin" on public.redemptions
  for select using (
    profile_id = auth.uid()
    or exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  );

-- Solicitudes de compra de puntos (transferencia Bre-B, confirmación manual del admin)
create table if not exists public.point_purchase_requests (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  points_requested numeric not null,
  reference text,
  status text not null default 'pendiente' check (status in ('pendiente','confirmado','rechazado')),
  created_at timestamptz default now(),
  resolved_by uuid references public.profiles(id),
  resolved_at timestamptz
);

alter table public.point_purchase_requests enable row level security;

create policy "purchase_requests_select_own_or_admin" on public.point_purchase_requests
  for select using (
    profile_id = auth.uid()
    or exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  );

create policy "purchase_requests_insert_own" on public.point_purchase_requests
  for insert with check (profile_id = auth.uid());

-- Configuración general de la app (ej. datos de cuenta Bre-B)
create table if not exists public.app_settings (
  key text primary key,
  value text
);

alter table public.app_settings enable row level security;

create policy "app_settings_select_all" on public.app_settings
  for select using (true);

create policy "app_settings_write_admin" on public.app_settings
  for all using (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  )
  with check (
    exists (select 1 from public.profiles p where p.id = auth.uid() and p.role = 'admin')
  );

insert into public.app_settings (key, value)
values ('brebe_info', 'Edita esta información desde Puntos → Datos de pago (Bre-B).')
on conflict (key) do nothing;

-- Ajusta el saldo de puntos de un cliente (solo admin)
create or replace function public.admin_adjust_points(p_profile_id uuid, p_amount numeric, p_note text)
returns void as $$
begin
  if not exists (select 1 from public.profiles where id = auth.uid() and role = 'admin') then
    raise exception 'Solo un administrador puede ajustar puntos';
  end if;

  update public.profiles set points_balance = points_balance + p_amount where id = p_profile_id;

  insert into public.point_movements (profile_id, amount, type, note, created_by)
  values (p_profile_id, p_amount, 'ajuste', p_note, auth.uid());
end;
$$ language plpgsql security definer;

-- Canjea un producto digital por puntos (cliente autenticado)
create or replace function public.redeem_digital_product(p_product_id uuid)
returns void as $$
declare
  v_price numeric;
  v_title text;
  v_balance numeric;
begin
  select points_price, title into v_price, v_title
  from public.digital_products where id = p_product_id and active = true;

  if v_price is null then
    raise exception 'Producto no disponible';
  end if;

  select points_balance into v_balance from public.profiles where id = auth.uid();

  if v_balance is null or v_balance < v_price then
    raise exception 'Saldo de puntos insuficiente';
  end if;

  update public.profiles set points_balance = points_balance - v_price where id = auth.uid();

  insert into public.redemptions (profile_id, product_id, product_title, points_spent)
  values (auth.uid(), p_product_id, v_title, v_price);

  insert into public.point_movements (profile_id, amount, type, note, created_by)
  values (auth.uid(), -v_price, 'redencion', v_title, auth.uid());
end;
$$ language plpgsql security definer;

-- Confirma una solicitud de compra de puntos y acredita el saldo (solo admin)
create or replace function public.confirm_point_purchase(p_request_id uuid)
returns void as $$
declare
  v_profile_id uuid;
  v_points numeric;
  v_status text;
begin
  if not exists (select 1 from public.profiles where id = auth.uid() and role = 'admin') then
    raise exception 'Solo un administrador puede confirmar compras';
  end if;

  select profile_id, points_requested, status into v_profile_id, v_points, v_status
  from public.point_purchase_requests where id = p_request_id;

  if v_status is null or v_status <> 'pendiente' then
    raise exception 'La solicitud no está pendiente';
  end if;

  update public.point_purchase_requests
  set status = 'confirmado', resolved_by = auth.uid(), resolved_at = now()
  where id = p_request_id;

  update public.profiles set points_balance = points_balance + v_points where id = v_profile_id;

  insert into public.point_movements (profile_id, amount, type, note, created_by)
  values (v_profile_id, v_points, 'compra', 'Compra de puntos vía Bre-B', auth.uid());
end;
$$ language plpgsql security definer;

-- Rechaza una solicitud de compra de puntos (solo admin)
create or replace function public.reject_point_purchase(p_request_id uuid)
returns void as $$
begin
  if not exists (select 1 from public.profiles where id = auth.uid() and role = 'admin') then
    raise exception 'Solo un administrador puede rechazar compras';
  end if;

  update public.point_purchase_requests
  set status = 'rechazado', resolved_by = auth.uid(), resolved_at = now()
  where id = p_request_id and status = 'pendiente';
end;
$$ language plpgsql security definer;

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
