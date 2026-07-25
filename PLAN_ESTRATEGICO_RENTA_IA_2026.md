# Plan Estratégico: Renta Recurrente con IA (Anthropic) — Versión Honesta
**Fecha:** 2026-07-24 · **Para:** Nilton Camargo / Pixadvisor · **Preparado por:** Claude

---

> ⚠️ **SUPERSEDIDO por [`PIXADVISOR_MONITOR_PLAN.md`](PIXADVISOR_MONITOR_PLAN.md) (2026-07-24).**
> Este borrador conserva válida la investigación de mercado (secciones 1-2), pero su propuesta
> técnica es **incorrecta**: proponía generalizar el pipeline de rásteres de la nube a multi-cliente.
> Al verificar el código, ese camino está cerrado (`ambientes.tif` no lo genera ningún script).
> El motor correcto es **PIX_ALERTA**. El precio propuesto acá (ticket bajo por lote) también está
> corregido en el plan nuevo. Leer el plan nuevo, no este.

---

## 1. El veredicto de la investigación (léelo antes del plan)

Investigué casos reales con evidencia, no promesas de gurús. El resultado es claro y conviene decirlo sin anestesia:

### Lo que NO funciona (el mito del "dinero 100% automático")
- **Canales YouTube "faceless" con IA:** tasa de éxito ~3%. Caso documentado: un creador invirtió $26.311 en 150 días y perdió casi $10.000. YouTube detecta y entierra contenido masivo de bajo esfuerzo, y desmonetiza.
- **Content farms / blogs IA / cuentas automatizadas:** Google y las plataformas los penalizan activamente. Es una carrera contra algoritmos que siempre pierde el pequeño.
- **"Agentes que generan dinero solos mientras dormís":** no existe ningún caso verificable. Todos los casos reales de ingreso con IA tienen un humano vendiendo, decidiendo y manteniendo relación con clientes. La automatización está en el *delivery*, nunca en la *venta*.
- **Regla de Anthropic (importante):** no se puede revender output de Claude sin contribución humana sustancial, ni usar la suscripción (Pro/Max) para servicios a terceros — para uso comercial se usa la **API con Commercial Terms**. Automatizar spam o contenido masivo viola la política de uso.

### Lo que SÍ funciona (con evidencia)
El patrón que se repite en todos los casos verificables:

> **Problema doloroso de un negocio + solución repetible + IA automatiza el 80-95% del delivery + un humano vende y da la cara.**

Casos documentados 2025-2026:
- Solo founder: **$41K MRR en 14 meses** automatizando autorizaciones previas de fisioterapia (workflow "aburrido" de un nicho vertical). Costo de modelo: <$4K/mes.
- Agencias de automatización IA de una persona: casos de **$25K a $2.7M ARR**; retainers de $10-15K/mes con clientes enterprise; margen bruto ~70% (servicios) → ~95% al productizar.
- Consultora IA: $12K MRR a los 11 meses; creador de productos digitales: ~$3.2K/mes pasivos con 12 templates (pero le tomó 6 meses de trabajo activo crearlos).
- Micro-SaaS: **70% ganan menos de $1K MRR**. Los que despegan resuelven un problema vertical específico, no "una app con IA".

**Conclusión:** "seguro y fiable" y "100% automático sin vos" son incompatibles. Lo alcanzable y real es: **ingreso recurrente donde la IA hace el 90% del trabajo y vos ponés 2-5 horas/semana de venta y supervisión.** Eso sí lo puedo construir casi entero.

---

## 2. La decisión estratégica: tu nicho ya está elegido

Dijiste "cualquier nicho". Error estratégico: en un nicho ajeno competís contra miles con la misma IA que vos. Tu ventaja injusta ya existe:

| Activo que YA tenés | Estado |
|---|---|
| Pipelines satelitales (vigor, anomalías, ambientes, sacarosa) validados en campo | Operativos |
| Monitoreo automático en la nube (GitHub Actions + GEE, trigo SA+SF) | **Ya corre solo desde 2026-07-19** |
| Skills de informes PDF de marca, propuestas ejecutivas | Operativos |
| Estrategia comercial ya definida: vender a CONSULTORES, no SaaS al productor | `project_renta_recurrente_online.md` |
| Cobro recurrente definido: Asaas + Pix Automático (BR) / Paddle (intl) | Definido |
| Clientes reales que validan el servicio (SA, SF, Cerro Alto, HDS) | Casos de éxito propios |

Ya tenés lo que el 99% de los que intentan "AI passive income" no tiene: **un producto que funciona, probado con clientes reales, con delivery ya automatizado.** Solo falta empaquetarlo y venderlo en serie.

---

## 3. El plan: "Pixadvisor Monitor" — servicio de monitoreo satelital automatizado para consultores agrónomos

**Modelo:** el consultor agrónomo (Brasil/Bolivia/Paraguay) paga una suscripción mensual por lote monitoreado. Cada semana/dékada, el sistema le entrega automáticamente: informe PDF de marca con alertas de anomalías (Gi* sobre residuo temporal, tu skill v8), mapa de vigor/ambientes, y aviso por WhatsApp/Telegram cuando hay foco que justifica scouting. **Él le cobra a su productor lo que quiera; vos sos su motor invisible.**

**Por qué este y no otro:**
- El delivery es 95% automatizable con lo que ya construimos (es literalmente el pipeline de monitoreo nube que ya corre para trigo SA+SF, generalizado).
- Precio piso NO es cero para consultores (a diferencia del productor, que recibe FieldView gratis de Bayer): el consultor compra *tiempo y diferenciación*, no píxeles.
- Cumple la política de Anthropic: API comercial, output con metodología propia (tu IP metodológica es el valor, no el texto de Claude).
- Es defendible: tus reglas metodológicas medidas (referencia temporal, MAD por fecha, cohortes, disponibilidad S2 48% medida en Santa Cruz) no las tiene nadie más.

### Precio orientativo (a validar en Fase 0)
- **Plan Consultor:** R$ 25-40 por lote/mes (mín. 10 lotes) → un consultor con 50 lotes = R$ 1.250-2.000/mes.
- Meta año 1: **10 consultores activos ≈ R$ 15-25K/mes** (≈ USD 3-5K/mes). Costo operativo: GEE (plan Limited) + API Claude + Actions ≈ <USD 200/mes.
- ⚠️ Al primer cliente que PAGA se dispara el registro de licencia comercial GEE (ya lo tenés anotado).

---

## 4. Fases (qué construyo yo, qué hacés vos)

### Fase 0 — Validación (semanas 1-2) · **vos: ~4 horas totales**
- **Yo construyo:** landing page del servicio (pixadvisor-web skill), PDF demo con datos reales de SA/SF anonimizados, guión de oferta por WhatsApp, lista de 30 consultores objetivo (scraping LinkedIn/CREA/directorios agro PR-SP-MT y Santa Cruz).
- **Vos hacés:** enviar 20-30 mensajes a consultores conocidos y de la lista. Meta: 3 que digan "sí, lo pagaría" → seguí. 0 → pivotamos antes de gastar un centavo.

### Fase 1 — Producto mínimo cobrable (semanas 3-6) · **vos: ~2 h/semana**
- **Yo construyo:**
  1. Generalización del pipeline de monitoreo nube: multi-cliente, multi-cultivo (config por consultor: GeoJSON de lotes + cultivo + fecha siembra).
  2. Informe PDF automático de marca por consultor (white-label opcional con SU logo).
  3. Alertas WhatsApp/Telegram automáticas (CallMeBot/bot, ya lo hicimos).
  4. Panel web simple para el consultor (ver lotes, histórico de informes) sobre el stack pix-admin existente.
  5. Documentación de alta de cliente en Asaas con Pix Automático.
- **Vos hacés:** onboarding de los 3 primeros consultores (llamada de 30 min c/u), crear la cuenta Asaas.

### Fase 2 — Automatizar la operación (semanas 7-10) · **vos: ~2 h/semana**
- **Yo construyo:**
  1. Onboarding self-service: el consultor sube su KMZ/GeoJSON, el sistema valida geometrías y activa el monitoreo solo.
  2. Agente de soporte nivel 1 (API Claude): responde dudas técnicas del consultor por WhatsApp con tu base metodológica; escala a vos solo lo que no puede.
  3. Facturación automática Asaas (webhook alta/baja/mora → activa/pausa monitoreo).
  4. Contenido de marketing continuo: 2 posts LinkedIn/semana generados desde los hallazgos reales del sistema (skill contenido-agro) — **vos aprobás antes de publicar** (regla: nada se publica sin tu OK).
- **Resultado:** operación diaria = 0 horas tuyas. Tu única tarea permanente: ventas y relación.

### Fase 3 — Escala (mes 3+)
- Canal socios: casas de insumos y biofábricas (Nova/Gil) que regalan el servicio a sus clientes técnicos.
- Segundo producto sobre la misma base instalada: muestreo dirigido (protocolo + puntos APK, ya lo tenés) y planificación de vuelos (skill V8) como add-ons.
- Paddle para cobrar fuera de Brasil (Bolivia/Paraguay/Argentina).

---

## 5. Qué NO voy a hacer (y por qué te protege)
- **No** voy a montar granjas de contenido, canales automáticos ni bots de redes: evidencia de fracaso masivo + violación de ToS + riesgo de baneo de cuentas.
- **No** voy a publicar, enviar mensajes ni cobrar a nadie sin tu aprobación explícita por acción.
- **No** prometo cifras: los números de la sección 3 son metas basadas en comparables, no garantías. Nadie honesto puede garantizar ingresos.

## 6. Riesgos reales y mitigación
| Riesgo | Mitigación |
|---|---|
| Consultores no pagan (precio piso bajo) | Fase 0 valida ANTES de construir; white-label les da diferenciación que sí pagan |
| Nubosidad (48% dékadas útiles S2 en SC) | Ya medido; S2∪S1 = 87%; el informe declara disponibilidad (honestidad = confianza) |
| GEE licencia comercial | Registrar plan Limited al primer pago (sin cuota mínima) |
| Dependencia de vos para ventas | Irreducible. 2-5 h/semana. Es el precio de que sea real y no humo |
| Churn de consultores | Alertas con valor accionable (umbral MIP, R$270/ha Embrapa) — el motor de alerta ya especificado es la Fase 3 natural |

---

## 7. Próximo paso inmediato
Si aprobás este plan, arranco Fase 0 ahora mismo: landing + PDF demo + lista de 30 consultores + guión de contacto. Todo queda listo para que vos solo tengas que apretar "enviar".

---

### Fuentes de la investigación
- [The Dark Reality Behind Faceless YouTube Automation Scams](https://buytrix.substack.com/p/the-dark-reality-behind-faceless)
- [The AI YouTube Automation Scam — Coping with Capitalism](https://medium.com/coping-with-capitalism/the-algorithm-ate-my-goldmine-24068ece5d53)
- [YouTube Automation Statistics 2026 — AutoFaceless](https://autofaceless.ai/blog/youtube-automation-statistics-2026)
- [The $41K MRR Boring-Workflow Playbook — Foundra](https://www.foundra.ai/key-reads/41k-mrr-boring-workflow-solo-vertical-ai-first-time-founder-2026)
- [How to Start an AI Automation Business: Real Case Studies $25K→$2.7M ARR — MindStudio](https://www.mindstudio.ai/blog/start-ai-automation-business-case-studies)
- [The Complete Guide To Productized Services 2026 — Assembly](https://assembly.com/blog/productized-services)
- [Solo founders using AI — Fortune](https://fortune.com/2026/05/18/solo-founders-ai-automation-entire-teams-entrepreneurs/)
- [Growing an AI orchestration platform to $3k MRR in 4 weeks — Indie Hackers](https://www.indiehackers.com/post/tech/growing-an-ai-orchestration-platform-to-3k-mrr-in-4-weeks-gK3zYDqQjXYG9ANwmxzA)
- [30 Micro SaaS Ideas Built by Solo Founders — VibrantSnap](https://www.vibrantsnap.com/blog/micro-saas-ideas-profitable-niches-2026)
- [Anthropic Usage Policy — launching a product with Claude](https://support.claude.com/en/articles/8241216-i-m-planning-to-launch-a-product-using-the-claude-api-what-steps-should-i-take-to-ensure-i-m-not-violating-anthropic-s-usage-policy)
- [Who Owns Claude's Outputs? — terms.law](https://terms.law/2024/08/24/who-owns-claudes-outputs-and-how-can-they-be-used/)
- [Anthropic bans subscription auth for third-party use — AlternativeTo](https://alternativeto.net/news/2026/2/anthropic-officially-bans-using-subscription-authentication-for-third-party-claude-use)
- [How to Make Money with AI in 2026: Real Case Studies — Humai](https://www.humai.blog/how-to-make-money-with-ai-in-2026-real-case-studies-proven-strategies-and-my-personal-journey/)
- [How To Make Money Using AI — Upwork](https://www.upwork.com/resources/make-money-with-ai)
