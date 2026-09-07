# Siigo · Panel de Negocio

Demo construido por **[Calybrat](https://calybrat.com)** para **Siigo**, la
compañía colombiana de software contable y administrativo para pymes y
contadores.

No es una plantilla con el logo cambiado. Es un panel diseñado alrededor de
cómo funciona Siigo: un SaaS de suscripción, con seis países, un canal de
contadores que distribuye el producto, una base heredada de adquisiciones que
hay que migrar, y una operación que se rompe al ritmo del calendario tributario
de la DIAN.

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Qué contesta el panel

| Módulo | La pregunta que responde |
|---|---|
| **Tablero Ejecutivo** | ¿Cómo va el negocio en una pantalla? |
| **ARR y Puente de Ingresos** | ¿De dónde sale y por dónde se va cada dólar de ARR? |
| **Retención, Fuga y Cohortes** | ¿Cuántos se van, por qué, y quiénes están a punto de irse? |
| **Adquisición y Unit Economics** | ¿Cuánto cuesta traer un cliente y en cuánto se paga? |
| **Planes, Precios y Módulos** | ¿Dónde está el ingreso y dónde el upsell sin vender? |
| **Canal de Contadores** | ¿Quién mueve la red de 35.000 contadores y quién se apagó? |
| **Expansión Regional** | ¿Cuál de los seis mercados merece el siguiente dólar? |
| **Migración Aspel → Nube** | ¿Cuánto vale terminar la migración de México, y cuánto cuesta la demora? |
| **Uso del Producto y Adopción** | ¿Quién usa qué, y quién dejó de entrar? |
| **Facturación Electrónica y DIAN** | ¿Cuánto volumen se mueve y por qué rechaza la DIAN? |
| **Plataforma y Confiabilidad** | ¿Aguanta el sistema los picos de temporada? |
| **Soporte y Experiencia** | ¿Por qué el soporte se rompe cinco meses al año? |
| **Finanzas y Regla del 40** | ¿Qué falta para el número que mira el fondo? |
| **Reportes Automáticos** | El informe mensual, generado solo |
| **Agente IA Siigo** | Preguntarle al negocio en español |

---

## Los datos

Son **simulados**, pero no inventados a ciegas. El modelo está anclado a cifras
públicas de Siigo y todo lo demás se deriva de ahí con supuestos de SaaS B2B
declarados explícitamente en [`data/generate_data.py`](data/generate_data.py).

### Anclas públicas usadas

| Dato | Fuente |
|---|---|
| Fundada en 1988 en Bogotá por Ricardo Ortiz y Fernando Rebellón; la dirige David Ortiz | [Colombia Fintech](https://colombiafintech.co/2025/08/06/de-empresa-familiar-a-una-de-las-plataformas-lideres-en-latinoamerica-asi-funciona-la-empresa-colombiana-siigo/) |
| Accel-KKR es el accionista desde 2017 | [Accel-KKR](https://www.accel-kkr.com/portfolio-company/siigo/) |
| Seis países: Colombia, México, Ecuador, Perú, Uruguay y Chile | [Siigo](https://www.siigo.com/) |
| +300.000 pymes y contadores activos en la plataforma | [Startups Latam](https://startupslatam.com/siigo-asegura-us1035-millones-para-acelerar-su-expansion-regional-y-seguir-digitalizando-las-pymes-de-latinoamerica/) |
| +120.000 pymes en Colombia · +35.000 contadores | [Guía de Software](https://www.guiadesoftware.com/software/siigo) · Accel-KKR |
| ~2.300 colaboradores | Colombia Fintech |
| Ingresos netos 2025: **+24,1%** | [Actualícese](https://actualicese.com/siigo-entre-las-empresas-de-mas-rapido-crecimiento-a-nivel-global-segun-endeavor-outliers-2026/) |
| Julio 2026: **US$103,5M** de financiación estructurada (Banco de Occidente, US$18,5M) | Startups Latam |
| Adquisiciones: Ilimitada (CO, 2019), Contífico (EC, 2020), Memory (UY, 2020), Aspel (MX, 2022) | [Accel-KKR](https://www.accel-kkr.com/colombia-based-siigo-expands-latin-american-footprint-with-acquisition-of-aspel-in-mexico/) · [Bloomberg Línea](https://www.bloomberglinea.com/2022/02/09/colombiana-siigo-compro-la-mexicana-aspel-e-invertira-us20-millones/) |
| Invierte más del 20% de los ingresos en producto | Accel-KKR |
| Precios Colombia 2026: Profesional Independiente $145.993, Emprendedor $191.327, Premium $207.869 (plan anual, por mes) | [Programas Contabilidad](https://programascontabilidad.com/comparativas-de-software/precios-de-software-contable-colombia-2026/) |
| Soporte calificado 6,5/10 por los usuarios, frente a 8,5 en funcionalidad | [Guía de Software](https://www.guiadesoftware.com/software/siigo) |

### Qué produce el modelo

Veintidós tablas, ventana de **24 meses** (sep 2024 – ago 2026), corte al
**31 de agosto de 2026**. Moneda de reporte: dólares, como corresponde a un
grupo con operación en seis monedas y accionista internacional.

- `clientes.csv.gz` — 167.640 clientes de Colombia con detalle nominal
- `contadores.csv` — los 35.800 del canal
- `suscripciones_mensual.csv` / `arr_puente.csv` — la base y el MRR, mes a mes
- `documentos.csv.gz` — emisión diaria ante la autoridad tributaria, 6 países
- `tickets.csv.gz` — 118.070 tickets de soporte (muestra 1 de cada 6)
- `uso_mensual.csv.gz` — panel de 12.000 clientes seguidos 24 meses
- …y las de finanzas, cohortes, embudo, NPS, plataforma, incidentes, adopción,
  migración de Aspel, competencia y headcount.

### La consistencia está garantizada por construcción

El MRR se **simula** mes a mes y el puente de ARR se **deriva** de esa
simulación, no al revés. Por eso

```
MRR[t] = MRR[t-1] + nuevo + expansión + reactivación − contracción − fuga
```

cierra exacto en todos los meses, países y planes. Y los indicadores que
aparecen en más de un módulo (NRR, GRR, churn, LTV/CAC, Regla del 40) se
calculan **una sola vez** en [`utils/datos.py`](utils/datos.py). Dos pantallas
no pueden dar cifras distintas del mismo indicador porque no hay dos cálculos.

Regenerar los datos:

```bash
python3 data/generate_data.py
```

El generador imprime al final una verificación contra las anclas públicas y
comprueba que el puente cierre.

---

## Identidad visual

Los colores no son una interpretación de la marca, salen de sus archivos:

| | |
|---|---|
| `#009DFF` | único hex declarado en el CSS de `siigo.com` |
| `#00A2FF` · `#00ABFF` | píxeles dominantes del logo y del lockup con eslogan |
| `#F28F17` | naranja del `+` en «+ que un software contable» |
| `#052E4A` | azul noche de la barra lateral y los titulares |

El logo de `assets/` es el SVG que sirve `siigo.com`, en tres versiones de color
generadas a partir del original. La **nube** que aparece en cada encabezado no
es decoración: el isotipo de Siigo *es* una nube y el producto se llama Siigo
Nube.

---

## El agente IA

Sin configurar nada, responde con lógica local sobre los mismos datos del panel
— la demostración funciona igual y las cifras coinciden con los tableros.

Para que converse con un modelo:

```toml
# .streamlit/secrets.toml   (nunca se commitea)
ANTHROPIC_API_KEY = "sk-ant-..."
```

El contexto que recibe el modelo se puede inspeccionar dentro del propio
módulo, en «Ver el contexto exacto que recibe el agente». Se arma con las mismas
funciones que alimentan los tableros, así que el agente no puede dar una cifra
distinta a la que muestra el panel.

---

## Pruebas

```bash
python3 pruebas.py
```

Abre los quince módulos con el runner headless de Streamlit y falla si alguno
lanza una excepción. Ejercita el código igual que el navegador: carga los datos,
arma las figuras y renderiza los widgets. Correrlo antes de cada despliegue
evita descubrir un `KeyError` en una demostración con el cliente.

---

## Registro de visitas

El demo es de acceso libre para que el cliente pueda abrirlo sin usuario ni
clave. Cada visita queda registrada con fecha, IP y ciudad aproximada. Ese
registro no se le muestra a nadie: aparece solo entrando con
`?accesos=calybrat` en la URL.

En Streamlit Cloud el registro se reinicia con cada despliegue, porque el
sistema de archivos es efímero.

---

## Estructura

```
siigo-demo/
├── app.py                  navegación y barra lateral
├── pruebas.py              prueba headless de los 15 módulos
├── assets/                 logo real de Siigo y banderas
├── data/
│   ├── generate_data.py    el modelo completo, con sus supuestos
│   └── *.csv, *.csv.gz     22 tablas
├── modules/p01…p15         un archivo por pantalla
└── utils/
    ├── formatters.py       paleta, CSS y componentes de marca
    ├── datos.py            carga cacheada e indicadores compartidos
    └── visitas.py          registro de accesos
```

---

**Datos simulados con fines de demostración.** Este panel no contiene
información confidencial de Siigo ni pretende representar sus cifras reales.
Construido por Calybrat como propuesta de producto.
