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
1. Descarga las 4 fuentes (stats, tipos, released, species) y las guarda en `data/raw/<fecha>/`.
2. Calcula el hash SHA-256 de cada fuente.
3. Compara los hashes con la ejecución anterior.
4. Regenera `pokeMAP.csv` con los datos frescos.
5. Compara el dataset anterior vs el actual y detecta:
   - Pokémon nuevos añadidos a GO.
   - Pokémon eliminados.
   - Pokémon con stats, tipos o nivel modificado.
6. Genera un reporte delta con fecha en `data/reports/delta_<run_id>.md`.
7. Sobreescribe `data/reports/last_delta.md` con el reporte más reciente.
8. Añade una línea al historial `data/metadata/hash_history.jsonl`.

**Frecuencia recomendada:** semanal o tras actualizaciones del juego.

---

### 2. `generate_pokemap_csv.py` ← generador simple (legacy)

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

## Columnas de `pokeMAP.csv`

| Columna | Valores posibles |
|---|---|
| Nombre | Nombre en inglés tal como aparece en GO |
| Tipo | Uno o dos tipos en español separados por `/` |
| Nivel | `normal` / `legendario` / `singular` / `desconocido` |
| Ataque Base | Número entero |
| Defensa Base | Número entero |
| Stamina Base | Número entero |
| fechaActualización | `YYYY-MM-DD` (fecha de extracción local) |

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

## Roadmap de mejoras pendientes en scripts

- [ ] Añadir columna `CategoriaGO` (mega, primigenio, ultraente, sombra...).
- [ ] Añadir score automático de utilidad (raids / gimnasio / PvP).
- [ ] Exportar también en formato `.xlsx` compatible con Excel.
- [ ] Añadir tests básicos para validar integridad del CSV generado.
