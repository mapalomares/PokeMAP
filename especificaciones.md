# PokeMAP - Especificaciones del Proyecto

> Última actualización: 2026-03-30

---

## 1. Resumen
PokeMAP será una aplicación para visualizar, organizar y gestionar la cuenta de Pokémon GO de Miguel Ángel Palomares (MAP).

---

## 2. Objetivo
Construir un MVP funcional para uso personal que permita centralizar la operativa diaria de la cuenta de Pokémon GO de MAP en una sola herramienta.

Objetivos concretos del MVP:
- Tener trazabilidad de capturas, evolución y progreso de colección.
- Gestionar inventario y recursos clave de forma rápida.
- Planificar tareas diarias/semanales del juego.
- Registrar ubicaciones útiles en mapa (gimnasios, poképaradas, rutas, nidos y eventos).

---

## 3. BBDD de Referencia Pokémon
La base de referencia es el primer pilar del proyecto. Permite determinar para cada Pokémon si es bueno y para qué (raids, gimnasios, PvP).

### Fuentes de datos
| Fuente | URL | Uso |
|---|---|---|
| PoGoAPI stats | `https://pogoapi.net/api/v1/pokemon_stats.json` | Ataque, Defensa, Stamina base |
| PoGoAPI tipos | `https://pogoapi.net/api/v1/pokemon_types.json` | Tipo(s) por forma |
| PoGoAPI released | `https://pogoapi.net/api/v1/released_pokemon.json` | Catálogo Pokémon disponibles en GO |
| PoGoAPI evolutions | `https://pogoapi.net/api/v1/pokemon_evolutions.json` | Evoluciones, caramelos y objeto requerido |
| PoGoAPI shadow | `https://pogoapi.net/api/v1/shadow_pokemon.json` | Disponibilidad de versión sombra |
| PoGoAPI raid bosses | `https://pogoapi.net/api/v1/raid_bosses.json` | Jefes de raid actuales |
| Veekun species CSV | `https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species.csv` | flags `is_legendary` e `is_mythical` |

### Columnas del CSV de referencia (`pokeMAP.csv`)
| Columna | Descripción |
|---|---|
| Nombre | Nombre del Pokémon |
| Tipo | Tipo(s) en español separados por `/` |
| NivelBase | `normal`, `legendario` o `singular` |
| CategoriaGO | categoría principal GO (`normal`, `legendario`, `singular`, `ultraente`, `bebe`) |
| EtiquetasGO | etiquetas auxiliares (`mega`, `primigenio`, `sombra`, `regional`, `bebe`) |
| esBebe | flag para valorar intercambios |
| Region | región exclusiva si aplica |
| Ataque Base | Stat base GO |
| Defensa Base | Stat base GO |
| Stamina Base | Stat base GO |
| ScorePvE | score heurístico 1-100 para PvE |
| ScorePvP_GL | score heurístico 1-100 para Gran Liga |
| ScorePvP_UL | score heurístico 1-100 para Ultra Liga |
| UsoPrincipal | recomendación automática (`raid`, `pve`, `pvp_gl`, `pvp_ul`, `coleccionable`) |
| Contadores | tipos contra los que es fuerte |
| EsRaid | si está en raids actuales |
| EvolucionaA | evoluciones directas |
| EvolucionRecomendada | mejor evolución por potencial total |
| UsoEvolucionRecomendada | uso principal de la evolución objetivo |
| ScoreEvolucionRecomendada | score total de la evolución objetivo |
| CosteCaramelosEvolucionRecomendada | caramelos acumulados para llegar a la evolución recomendada |
| ObjetosEvolucionRecomendada | objetos necesarios para la ruta evolutiva recomendada |
| fechaActualizacion | Fecha de la última extracción |

### Sobre la clasificación de nivel y evolución
- `is_legendary` → **legendario**
- `is_mythical` → **singular**
- Resto → **normal**
- Las formas primigenias (Groudon, Kyogre) se detectan en `mega_pokemon.json`.
- Coste de evolución se calcula en base a `pokemon_evolutions.json`:
  - `candy_required` por salto.
  - `item_required` (ejemplo: Sinnoh Stone, Metal Coat, Upgrade).
- Se calcula coste acumulado de caramelos y objetos para llegar al objetivo recomendado.

### Estrategia de actualización y control de cambios
- Cada ejecución del script de sincronización:
  1. Descarga y guarda un snapshot crudo fechado en `data/raw/<run_id>/`.
  2. Calcula hash SHA-256 por fuente y compara con la ejecución previa.
  3. Si hay cambios en algún hash, genera un reporte delta en `data/reports/`.
  4. El historial acumulado de hashes se mantiene en `data/metadata/hash_history.jsonl`.
- No hay fecha de fuente (las APIs no la exponen); la trazabilidad se garantiza via hashes + snapshots locales.

---

## 4. Scripts Python
| Script | Función |
|---|---|
| `generate_pokemap_csv.py` | Generador simple: descarga fuentes y escribe `pokeMAP.csv`. |
| `sync_pokemap_reference.py` | Script principal: descarga, hashes, delta, snapshots, CSV y XLSX. Usar este en producción. |
| `check_pokemon.py` | Consulta rápida por nombre: utilidad, scores y recomendación evolutiva con coste. |

### App iPhone sin cuenta Apple Developer
- Se implementa como PWA en `docs/` (instalable desde Safari).
- Interfaz simple: escribes nombre y devuelve resultado equivalente al script Python.
- Datos locales en `docs/data/pokeMAP.csv` sincronizados por `sync_pokemap_reference.py`.

---

## 5. Estructura del Proyecto
```
PokeMAP/
├── especificaciones.md         # Este documento
├── instrucciones.md            # Guía de uso y operación
├── pokeMAP.csv                 # BBDD de referencia generada
├── generate_pokemap_csv.py     # Generador simple (legacy)
├── sync_pokemap_reference.py   # Script de sincronización completo
├── data/
│   ├── raw/<run_id>/           # Snapshots crudos por ejecución
│   ├── metadata/               # Hashes y datasets por ejecución
│   └── reports/                # Reportes delta (Markdown)
├── tmp/                        # Archivos temporales (ignorados por git)
├── docs/                       # PWA instalable para iPhone
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── manifest.webmanifest
│   ├── sw.js
│   └── data/pokeMAP.csv
├── frontend/                   # Reservado para evolución futura
└── backend/                    # API REST (futuro, fase 2)
```

---

## 6. Git y Respaldo en GitHub
- Repositorio: cuenta GitHub de mapalomares@gmail.com → `PokeMAP`
- Rama principal: `main`
- Los snapshots crudos en `data/raw/` se incluyen en git para trazabilidad histórica.
- La carpeta `tmp/` está excluida vía `.gitignore`.

---

## 7. Próximos Pasos
- Mejorar fórmula de scoring con movimientos reales y rankings PvP externos (PvPoke).
- Añadir filtros por presupuesto de caramelos/objetos en `check_pokemon.py` y PWA.
- Publicar PWA en hosting HTTPS compatible con instalación iPhone.
- Añadir persistencia de tu caja personal para comparar "lo que tienes" vs "lo ideal".
