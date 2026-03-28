# PokeMAP - Especificaciones del Proyecto

> Última actualización: 2026-03-28

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
| Veekun species CSV | `https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species.csv` | flags `is_legendary` e `is_mythical` |

### Columnas del CSV de referencia (`pokeMAP.csv`)
| Columna | Descripción |
|---|---|
| Nombre | Nombre del Pokémon |
| Tipo | Tipo(s) en español separados por `/` |
| Nivel | `normal`, `legendario` o `singular` |
| Ataque Base | Stat base GO |
| Defensa Base | Stat base GO |
| Stamina Base | Stat base GO |
| fechaActualización | Fecha de la última extracción |

### Sobre la clasificación de Nivel
- `is_legendary` → **legendario**
- `is_mythical` → **singular**
- Resto → **normal**
- Las formas primigenias (Groudon, Kyogre) y mega no tienen flag `is_primal`; aparecen como formas en `mega_pokemon.json` de PoGoAPI. Se modelarán como columna `CategoriaGO` en versiones futuras.

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
| `sync_pokemap_reference.py` | Script principal: descarga, hashes, delta, snapshots y CSV. Usar este en producción. |

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
├── docs/                       # Documentación adicional (futuro)
├── frontend/                   # Aplicación web (futuro)
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
- Añadir columna `CategoriaGO` (mega, primigenio, ultraente, sombra, etc.) al CSV.
- Definir criterio automático de "bueno para qué" (score raids, gimnasio, PvP).
- Definir esquema de datos para colección personal, tareas e inventario.
- Montar estructura base de frontend con navegación por módulos.
- Crear primer prototipo de dashboard + mapa + checklist de tareas.
