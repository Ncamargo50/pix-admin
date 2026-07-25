-- PIX Scout — backend de validaciones de campo (Supabase / PostgreSQL)
-- Ejecutar UNA VEZ en el SQL Editor del proyecto Supabase.
--
-- CONTEXTO DE SEGURIDAD (leer antes de tocar las policies):
-- La SUPABASE_ANON_KEY viaja DENTRO del APK. Es publica por construccion: cualquiera
-- que instale la app la tiene. Por eso este esquema es APPEND-ONLY para anon:
--   - INSERT  si  (es el registro del tecnico saliendo del campo)
--   - SELECT  NO  (con la anon key nadie puede volcarse la tabla entera)
--   - UPDATE  NO  (una validacion de campo es inmutable: es un dato observado)
--   - DELETE  NO
-- Leer los datos se hace con la service_role key desde el pipeline, nunca desde la app.
-- Esto evita repetir el defecto ya detectado en pix-muestreo (anon podia leer
-- password_hash, RLS con `using (true)`).
--
-- Los nombres de columna son EXACTAMENTE las claves que manda la app (camelCase
-- incluido). PostgREST mapea clave JSON -> columna; si una no existe, el POST falla
-- entero con PGRST204 y la validacion queda en la cola para siempre.

create table if not exists public.scout_validaciones (
  -- identidad
  id                text primary key,          -- generado offline por el telefono (Store.uid)
  created           timestamptz not null default now(),

  -- de que aviso vino (sin esto la precision del motor no tiene numerador)
  "focoId"          text,
  "focoIdEstable"   boolean,
  estrato           text,                      -- nivel de alerta del satelite. Se GUARDA y no se muestra
  hacienda          text,
  lote              text,
  "fechaImg"        text,                      -- fecha de la escena que origino el aviso

  -- que se encontro
  hallazgo          text,                      -- 'nada' = registro negativo, el que mide falsos positivos
  categoria         text,
  "fichaId"         text,
  alcance           text,                      -- Punto / Recorrido parcial / Lote completo
  cultivo           text,
  nombre            text,
  cientifico        text,
  estadio           text,
  severidad         text,
  incidencia        text,

  -- conteo y umbral MIP
  conteo            numeric,
  conteo_unidad     text,
  umbral_texto      text,
  umbral_fuente     text,
  -- under | at | over. Es el CRITERIO DEL TECNICO, y desde el bloqueante 4 solo se pide
  -- donde la plaga NO tiene umbral computable. Es una opinion y se guarda como tal.
  nde               text,
  -- Veredicto CALCULADO por umbral.js. null = no se pudo calcular; `umbral_estado`
  -- dice por que. OJO: null NO significa "no supera" — no rellenar por descarte.
  supera_umbral     boolean,
  umbral_estado     text,                      -- supera | por_debajo | referencia_* | sin_conteo | ...
  umbral_calculado  boolean,
  -- false cuando el punto lo eligio el satelite: el umbral MIP esta calibrado sobre
  -- muestreo REPRESENTATIVO. Filtrar por esta columna antes de agregar conteos, o el
  -- analisis concluye que hace falta aplicar mas de lo que hace falta.
  umbral_comparable_mip boolean,
  umbral_regla      text,                      -- JSON de la regla aplicada (valor/operador/unidad)
  -- PUERTA 4.3 — ciego auditable. `registro_a_ciegas` es la unica columna con la que se
  -- puede DEMOSTRAR, al cierre de la campaña, que el tecnico no vio el nivel de alerta
  -- antes de registrar. Un ciego que se confia al procedimiento no lo puede verificar
  -- un tercero, y una campaña que no se puede auditar no prueba nada.
  modo_ciego        boolean,                   -- estaba encendido al registrar
  estrato_visto_en  text,                      -- cuando la pantalla revelo el estrato (ISO), o null
  registro_a_ciegas boolean,                   -- ciego encendido Y estrato nunca revelado
  coincide          text,
  -- 'dirigido_satelital': el satelite eligio el sitio (el peor punto del lote). El umbral
  -- MIP esta calibrado sobre muestreo REPRESENTATIVO: este conteo no es comparable con el.
  -- La columna existe para que ningun analisis los mezcle por accidente.
  tipo_muestreo     text,

  -- donde y quien
  coord             text,                      -- 'lat, lon' con 5 decimales, o '—' si no hubo fix
  acc               integer,                   -- precision GPS en metros
  gps_real          boolean,                   -- false = la coordenada es la del foco, NO la del tecnico
  tecnico           text,
  cliente           text,

  observacion       text,
  foto              text                       -- data URL base64. Ver nota de tamaño al pie
);

comment on table public.scout_validaciones is
  'Lazo de retorno de PIX Scout: lo que el tecnico encontro al llegar al foco. Append-only.';

create index if not exists scout_val_foco_idx    on public.scout_validaciones ("focoId");
create index if not exists scout_val_created_idx on public.scout_validaciones (created desc);
create index if not exists scout_val_hac_idx     on public.scout_validaciones (hacienda, created desc);

-- ---------------------------------------------------------------------------
-- RLS: append-only para la app
-- ---------------------------------------------------------------------------
alter table public.scout_validaciones enable row level security;

drop policy if exists scout_val_insert_anon on public.scout_validaciones;
create policy scout_val_insert_anon
  on public.scout_validaciones
  for insert
  to anon, authenticated
  with check (
    -- minimos que hacen util al registro. Sin tecnico o sin hallazgo la fila no sirve
    -- para medir nada, y aceptar basura silenciosamente es peor que rechazarla.
    id is not null
    and length(id) between 4 and 64
    and hallazgo is not null
    and tecnico  is not null
    -- techo de tamaño: la foto es base64 y un POST sin limite es un vector de abuso
    -- con una clave que es publica. 3 MB alcanza para una foto de celular comprimida.
    and (foto is null or length(foto) < 3145728)
    and (observacion is null or length(observacion) < 4000)
  );

-- NO se crean policies de select/update/delete a proposito: sin policy, RLS niega.
-- Para leer, usar la service_role key (server-side), nunca la anon.

-- ---------------------------------------------------------------------------
-- Vista de analisis (service_role): coordenada parseada y listo para cruzar
-- ---------------------------------------------------------------------------
create or replace view public.scout_validaciones_geo as
select
  v.*,
  nullif(split_part(v.coord, ',', 1), '')::double precision as lat,
  nullif(trim(split_part(v.coord, ',', 2)), '')::double precision as lon,
  (v.hallazgo = 'nada') as es_registro_negativo
from public.scout_validaciones v
where v.coord ~ '^-?[0-9]+\.[0-9]+,\s*-?[0-9]+\.[0-9]+$';

comment on view public.scout_validaciones_geo is
  'Validaciones con coordenada parseable. Las filas sin fix GPS quedan FUERA a proposito: '
  'una coordenada que en realidad es la del foco no es evidencia de donde estuvo el tecnico.';

-- ---------------------------------------------------------------------------
-- NOTA sobre `foto`
-- ---------------------------------------------------------------------------
-- Guardar base64 en una columna funciona y es lo mas simple para arrancar, pero infla
-- la tabla ~33% sobre el tamaño del archivo y hace lentos los dumps. Cuando el volumen
-- lo justifique (>~2.000 validaciones), mover a Supabase Storage y dejar aca la ruta.
-- No se hace ahora para no meter un segundo punto de falla antes del ensayo de campo.
