# PokeMAP - Instrucciones de Uso y Operación

> Última actualización: 2026-03-28

---

## Requisitos previos
- Python 3.10+
- `curl` disponible en PATH (viene por defecto en macOS)
- Conexión a internet para descarga de fuentes

---

## Scripts disponibles

### 1. `sync_pokemap_reference.py` ← usar este en el día a día

Script principal de sincronización. Hace todo el ciclo:

```bash
python3 sync_pokemap_reference.py
```

**Qué hace en orden:**
1. Descarga las 7 fuentes (stats, tipos, released, mega, shadow, raids, species) y las guarda en `data/raw/<fecha>/`.
2. Calcula el hash SHA-256 de cada fuente.
3. Compara los hashes con la ejecución anterior.
4. Regenera `pokeMAP.csv` y `pokeMAP.xlsx` con los datos frescos.
5. Compara el dataset anterior vs el actual y detecta:
   - Pokémon nuevos añadidos a GO.
   - Pokémon eliminados.
   - Pokémon con stats, tipos, scores o nivel modificado.
6. Genera un reporte delta con fecha en `data/reports/delta_<run_id>.md`.
7. Sobreescribe `data/reports/last_delta.md` con el reporte más reciente.
8. Añade una línea al historial `data/metadata/hash_history.jsonl`.

**Frecuencia recomendada:** semanal o tras actualizaciones del juego.

---

### 2. `check_pokemon.py` ← consulta visual rápida

Busca un Pokémon por nombre y muestra su utilidad, scores y recomendación de uso.

```bash
python3 check_pokemon.py <nombre_pokemon>
```

**Ejemplos:**
```bash
python3 check_pokemon.py mewtwo
python3 check_pokemon.py blissey
python3 check_pokemon.py "Mr. Mime"
python3 check_pokemon.py togepi
```

**Output incluye:**
- ✅ Clasificación (tipo, nivel, categoría GO, etiquetas)
- 💪 Stats base (Ataque, Defensa, Stamina)
- 📊 Scores para PvE, PvP GL y PvP UL (coloreados dinámicamente)
- ✅ Recomendación de uso principal (raid/pve/pvp_gl/pvp_ul/coleccionable)
- 💥 Tipos contra los que es fuerte
- 🛡️ Detección si está en raids activos
- 👶 Nota si es Pokémon Bebé (valioso para intercambio)

---

### 3. `generate_pokemap_csv.py` ← generador simple (legacy)

Versión simplificada sin control de cambios. Solo descarga y genera el CSV.

```bash
python3 generate_pokemap_csv.py
```

Útil si solo quieres regenerar el CSV rápidamente sin registrar cambios.

---

## Archivos generados

| Ruta | Descripción |
|---|---|
| `pokeMAP.csv` | BBDD de referencia lista para usar |
| `data/raw/<run_id>/` | Snapshots crudos de cada fuente por ejecución |
| `data/metadata/latest_hashes.json` | Hashes de la última ejecución |
| `data/metadata/latest_dataset.json` | Dataset completo de la última ejecución |
| `data/metadata/hash_history.jsonl` | Historial acumulado de hashes por ejecución |
| `data/reports/last_delta.md` | Último reporte de cambios |
| `data/reports/delta_<run_id>.md` | Reporte histórico por ejecución |

---

## Cómo saber si algo cambió en las fuentes

1. Ejecuta `sync_pokemap_reference.py`.
2. Abre `data/reports/last_delta.md`.
3. Revisa la sección **Fuentes cambiadas**:
   - Si está vacía → no ha cambiado nada, no hace falta revisar el CSV.
   - Si lista fuentes → revisa las secciones de IDs nuevos, eliminados y campos modificados.

También puedes revisar el historial acumulado:

```bash
cat data/metadata/hash_history.jsonl
```

---

## Columnas de `pokeMAP.csv` y `pokeMAP.xlsx`

| Columna | Valores posibles | Descripción |
|---|---|---|
| Nombre | Texto | Nombre en inglés tal como aparece en GO |
| Tipo | uno/dos tipos en español | Separados por `/` |
| NivelBase | `normal` / `legendario` / `singular` / `desconocido` | Clasificación base de especie |
| CategoriaGO | `normal` / `bebe` / `legendario` / `singular` / `ultraente` | Categoría específica de GO |
| EtiquetasGO | Multi-etiqueta | Combinación de: mega, primigenio, sombra, regional, bebe |
| esBebe | `sí` / `no` | Flag is_baby para intercambio valioso |
| Region | Región o vacío | Para Pokémon con exclusividad regional |
| Ataque Base | Número entero | Stat base GO |
| Defensa Base | Número entero | Stat base GO |
| Stamina Base | Número entero | Stat base GO |
| ScorePvE | 1-100 | Score para contenido offline (énfasis en ataque) |
| ScorePvP_GL | 1-100 | Score para Gran Liga (CP ≤1500, énfasis en balance) |
| ScorePvP_UL | 1-100 | Score para Ultra Liga (CP ≤2500, más ataque) |
| UsoPrincipal | raid/pve/pvp_gl/pvp_ul/coleccionable | Recomendación automática de uso |
| Contadores | Tipos (hasta 3) | Tipos vs los que este Pokémon es fuerte |
| EsRaid | `sí` / `no` | Si está en raids activos de PoGoAPI |
| fechaActualizacion | `YYYY-MM-DD` | Fecha de sincronización local |

> ⚠️ La fecha es la del día en que ejecutas el script, no la que publica la API (las APIs públicas no exponen fecha de actualización).

---

## Respaldo en GitHub

El repositorio está en: https://github.com/mapalomares/PokeMAP

Para subir cambios:

```bash
git add .
git commit -m "feat: <descripción del cambio>"
git push
```

Para crear un commit de sincronización de datos:

```bash
git add pokeMAP.csv data/
git commit -m "data: sync referencia $(date +%Y-%m-%d)"
git push
```

---

## Roadmap de mejoras pendientes

- [x] Añadir columna `CategoriaGO` (mega, primigenio, ultraente, sombra...). ✓ v2
- [x] Añadir score automático de utilidad (PvE / PvP GL / PvP UL). ✓ v3
- [x] Exportar también en formato `.xlsx` compatible con Excel. ✓ v2.1
- [x] Script visual para consultar Pokémon rápidamente. ✓ check_pokemon.py
- [x] Detección automática de raid bosses actuales. ✓ v3
- [x] Tabla de efectividad y contadores de tipos. ✓ v3
- [ ] Integración con PvPoke API para rankings PvP más precisos.
- [ ] Filtros avanzados en `check_pokemon.py` (--min-score-pve, --tipo, etc).
- [ ] Persistencia local de capturas personales (DB SQLite).
- [ ] Dashboard web interactivo.
- [ ] Tests automatizados para validar integridad del CSV.

