#!/usr/bin/env python3
# sync_pokemap_reference.py  — v2.1
# Columnas nuevas: NivelBase, CategoriaGO, EtiquetasGO, esBebe, Region
# Export: CSV + Excel (pokeMAP.xlsx)
import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


SOURCES = {
    "pokemon_stats": "https://pogoapi.net/api/v1/pokemon_stats.json",
    "pokemon_types": "https://pogoapi.net/api/v1/pokemon_types.json",
    "released_pokemon": "https://pogoapi.net/api/v1/released_pokemon.json",
    "mega_pokemon": "https://pogoapi.net/api/v1/mega_pokemon.json",
    "shadow_pokemon": "https://pogoapi.net/api/v1/shadow_pokemon.json",
    "pokemon_species_csv": "https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species.csv",
}

# IDs de Ultra Bestias (estables entre generaciones)
ULTRA_BEAST_IDS = {793, 794, 795, 796, 797, 798, 799, 803, 804, 805, 806}

# Regionales en Pokémon GO: {pokemon_id: "Región"}
# Fuente: conocimiento consolidado de la comunidad GO (aproximado, cambia con eventos)
REGIONAL_MAP = {
    # Gen 1
    83:  "Asia Oriental",
    115: "Australia / Nueva Zelanda",
    122: "Europa",
    128: "Norteamérica",
    # Gen 2
    214: "Sudamérica / Sur de EEUU",
    222: "Regiones tropicales",
    313: "Europa / Asia / Pacífico",
    314: "América / África",
    # Gen 3
    324: "Sur de Asia",
    335: "Europa / Asia / Pacífico",
    336: "América / África",
    337: "América / África",
    338: "Europa / Asia / Pacífico",
    357: "África / Sur de Europa",
    369: "Nueva Zelanda / Oceanía",
    # Gen 4
    417: "Canadá / Norte de EEUU",
    422: "Global (formas por región)",  # Shellos
    423: "Global (formas por región)",  # Gastrodon
    439: "Europa",
    441: "Hemisferio Sur",
    455: "Sureste de EEUU",
    # Legendarios regionales (raids, no captura libre)
    480: "Asia-Pacífico",   # Uxie
    481: "Europa/África",   # Mesprit
    482: "América",         # Azelf
    # Gen 5
    538: "Europa / Asia / Pacífico",
    539: "América / África",
    556: "América",
    561: "Egipto / Grecia",
    626: "Norteamérica",
    631: "América / África / Oriente Medio",
    632: "Europa / Asia / Pacífico",
    # Gen 6
    707: "Asia",            # Klefki
    # Gen 7
    741: "Global (formas por región)",  # Oricorio
    # Gen 8
    865: "Gallar/Reino Unido",  # Sirfetch'd (event, no estrictamente regional)
    875: "Global",              # Eiscue
    # Gen 9 (expandir según disponibilidad GO)
}

TYPE_ES = {
    "Normal": "normal",
    "Fire": "fuego",
    "Water": "agua",
    "Electric": "electrico",
    "Grass": "planta",
    "Ice": "hielo",
    "Fighting": "lucha",
    "Poison": "veneno",
    "Ground": "tierra",
    "Flying": "volador",
    "Psychic": "psiquico",
    "Bug": "bicho",
    "Rock": "roca",
    "Ghost": "fantasma",
    "Dragon": "dragon",
    "Dark": "siniestro",
    "Steel": "acero",
    "Fairy": "hada",
}


def ensure_dirs():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/metadata", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)


def run_curl(url, output_path):
    subprocess.run(["curl", "-fsSL", url, "-o", output_path], check=True)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_species_data(path):
    """Devuelve dict {pid: {nivel_base, es_bebe}} desde el CSV de especies."""
    data = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pid = int(row["id"])
            except Exception:
                continue
            is_legendary = row.get("is_legendary", "0") == "1"
            is_mythical = row.get("is_mythical", "0") == "1"
            is_baby = row.get("is_baby", "0") == "1"
            if is_mythical:
                nivel = "singular"
            elif is_legendary:
                nivel = "legendario"
            else:
                nivel = "normal"
            data[pid] = {"nivel_base": nivel, "es_bebe": is_baby}
    return data


def pick_preferred_form(rows):
    by_id = {}
    for row in rows:
        pid = int(row["pokemon_id"])
        current = by_id.get(pid)
        if current is None or row.get("form") == "Normal":
            by_id[pid] = row
    return by_id


def build_mega_sets(mega_data):
    """Devuelve (set_ids_con_mega, set_ids_con_primigenio)."""
    mega_ids = set()
    primal_ids = set()
    for entry in mega_data:
        pid = int(entry["pokemon_id"])
        mega_ids.add(pid)
        if "primal" in entry.get("mega_name", "").lower():
            primal_ids.add(pid)
    return mega_ids, primal_ids


def build_shadow_set(shadow_data):
    """Devuelve set de IDs con forma sombra disponible en GO."""
    return {int(k) for k in shadow_data.keys()}


def build_rows(stats, types, released, mega_data, shadow_data, species_data):
    stats_by_id = pick_preferred_form(stats)
    types_by_id = pick_preferred_form(types)
    mega_ids, primal_ids = build_mega_sets(mega_data)
    shadow_ids = build_shadow_set(shadow_data)

    fecha = datetime.now().strftime("%Y-%m-%d")
    rows = []

    for pid_str, released_info in released.items():
        pid = int(pid_str)
        st = stats_by_id.get(pid)
        tp = types_by_id.get(pid)
        if st is None:
            continue

        sp = species_data.get(pid, {})
        nivel_base = sp.get("nivel_base", "desconocido")
        es_bebe = sp.get("es_bebe", False)

        # CategoriaGO: clasificación jerárquica GO-específica
        if pid in ULTRA_BEAST_IDS:
            categoria_go = "ultraente"
        elif nivel_base == "singular":
            categoria_go = "singular"
        elif nivel_base == "legendario":
            categoria_go = "legendario"
        elif es_bebe:
            categoria_go = "bebe"
        else:
            categoria_go = "normal"

        # EtiquetasGO: multi-etiqueta separada por comas
        etiquetas = []
        if es_bebe:
            etiquetas.append("bebe")
        if pid in mega_ids:
            etiquetas.append("mega")
        if pid in primal_ids:
            etiquetas.append("primigenio")
        if pid in shadow_ids:
            etiquetas.append("sombra")
        if pid in REGIONAL_MAP:
            etiquetas.append("regional")

        # Región (solo para regionales)
        region = REGIONAL_MAP.get(pid, "")

        tipo_raw = tp.get("type", []) if tp else []
        tipo = "/".join(TYPE_ES.get(t, t.lower()) for t in tipo_raw) if tipo_raw else "desconocido"
        nombre = st.get("pokemon_name") or released_info.get("name") or f"Pokemon {pid}"

        rows.append(
            {
                "id": pid,
                "Nombre": nombre,
                "Tipo": tipo,
                "NivelBase": nivel_base,
                "CategoriaGO": categoria_go,
                "EtiquetasGO": ",".join(etiquetas),
                "esBebe": "sí" if es_bebe else "no",
                "Region": region,
                "Ataque Base": st.get("base_attack", ""),
                "Defensa Base": st.get("base_defense", ""),
                "Stamina Base": st.get("base_stamina", ""),
                "fechaActualizacion": fecha,
            }
        )

    rows.sort(key=lambda r: r["id"])
    return rows


CSV_FIELDS = [
    "Nombre",
    "Tipo",
    "NivelBase",
    "CategoriaGO",
    "EtiquetasGO",
    "esBebe",
    "Region",
    "Ataque Base",
    "Defensa Base",
    "Stamina Base",
    "fechaActualizacion",
]

SNAPSHOT_FIELDS = ["Nombre", "Tipo", "NivelBase", "CategoriaGO", "EtiquetasGO",
                   "esBebe", "Region", "Ataque Base", "Defensa Base", "Stamina Base"]


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in CSV_FIELDS})


def write_excel(rows, path):
    """Escribe el CSV a un archivo .xlsx con estilos básicos. Requiere openpyxl."""
    if not HAS_OPENPYXL:
        print(f"⚠️  openpyxl no está instalado. Skipping {path}")
        print("   Para habilitar: pip install openpyxl")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "PokeMAP"

    # Header con estilos
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for col_idx, field in enumerate(CSV_FIELDS, 1):
        cell = ws.cell(row=1, column=col_idx, value=field)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Datos
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, field in enumerate(CSV_FIELDS, 1):
            value = row_data.get(field, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = border
            # Color alternado para mejor legibilidad
            if row_idx % 2 == 0:
                cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")

    # Auto-ajuste de anchos
    ws.column_dimensions["A"].width = 20  # Nombre
    ws.column_dimensions["B"].width = 15  # Tipo
    ws.column_dimensions["C"].width = 12  # NivelBase
    ws.column_dimensions["D"].width = 14  # CategoriaGO
    ws.column_dimensions["E"].width = 25  # EtiquetasGO
    ws.column_dimensions["F"].width = 8   # esBebe
    ws.column_dimensions["G"].width = 25  # Region
    ws.column_dimensions["H"].width = 12  # Ataque Base
    ws.column_dimensions["I"].width = 12  # Defensa Base
    ws.column_dimensions["J"].width = 12  # Stamina Base
    ws.column_dimensions["K"].width = 16  # fechaActualizacion

    # Freeze panes en header
    ws.freeze_panes = "A2"

    wb.save(path)
    print(f"✓ Excel generado: {path}")


def rows_by_id(rows):
    out = {}
    for row in rows:
        out[str(row["id"])] = {f: row[f] for f in SNAPSHOT_FIELDS}
    return out


def diff_hashes(previous, current):
    if not previous:
        return list(current.keys())
    changed = []
    for key, digest in current.items():
        if previous.get(key) != digest:
            changed.append(key)
    return sorted(changed)


def diff_rows(previous_rows, current_rows):
    prev_ids = set(previous_rows.keys())
    curr_ids = set(current_rows.keys())
    added = sorted(curr_ids - prev_ids, key=lambda x: int(x))
    removed = sorted(prev_ids - curr_ids, key=lambda x: int(x))

    changed = []
    shared = sorted(prev_ids & curr_ids, key=lambda x: int(x))
    for pid in shared:
        old = previous_rows[pid]
        new = current_rows[pid]
        field_changes = {}
        for field in SNAPSHOT_FIELDS:
            if old.get(field) != new.get(field):
                field_changes[field] = {"old": old.get(field), "new": new.get(field)}
        if field_changes:
            changed.append({"id": int(pid), "changes": field_changes})

    return added, removed, changed


def write_report(path, now_iso, source_changes, added, removed, changed):
    lines = []
    lines.append("# Delta PokeMAP")
    lines.append("")
    lines.append(f"- Fecha ejecucion UTC: {now_iso}")
    lines.append(f"- Fuentes con hash cambiado: {len(source_changes)}")
    lines.append(f"- Pokemon nuevos: {len(added)}")
    lines.append(f"- Pokemon eliminados: {len(removed)}")
    lines.append(f"- Pokemon modificados: {len(changed)}")
    lines.append("")

    if source_changes:
        lines.append("## Fuentes cambiadas")
        for src in source_changes:
            lines.append(f"- {src}")
        lines.append("")

    if added:
        lines.append("## IDs nuevos")
        lines.append("- " + ", ".join(added[:50]))
        if len(added) > 50:
            lines.append(f"- ... y {len(added) - 50} mas")
        lines.append("")

    if removed:
        lines.append("## IDs eliminados")
        lines.append("- " + ", ".join(removed[:50]))
        if len(removed) > 50:
            lines.append(f"- ... y {len(removed) - 50} mas")
        lines.append("")

    if changed:
        lines.append("## Cambios de campos (muestra)")
        for item in changed[:100]:
            lines.append(f"- ID {item['id']}: {json.dumps(item['changes'], ensure_ascii=False)}")
        if len(changed) > 100:
            lines.append(f"- ... y {len(changed) - 100} cambios mas")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ensure_dirs()

    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%d_%H%M%SZ")
    now_iso = now.isoformat()

    raw_dir = os.path.join("data/raw", run_id)
    os.makedirs(raw_dir, exist_ok=True)

    local_files = {}
    hashes = {}

    for name, url in SOURCES.items():
        ext = ".json" if name != "pokemon_species_csv" else ".csv"
        dst = os.path.join(raw_dir, f"{name}{ext}")
        run_curl(url, dst)
        local_files[name] = dst
        hashes[name] = sha256_file(dst)

    stats = load_json(local_files["pokemon_stats"])
    types = load_json(local_files["pokemon_types"])
    released = load_json(local_files["released_pokemon"])
    mega_data = load_json(local_files["mega_pokemon"])
    shadow_data = load_json(local_files["shadow_pokemon"])
    species_data = load_species_data(local_files["pokemon_species_csv"])

    rows = build_rows(stats, types, released, mega_data, shadow_data, species_data)
    write_csv(rows, "pokeMAP.csv")
    write_excel(rows, "pokeMAP.xlsx")
    current_rows = rows_by_id(rows)

    latest_hashes_path = "data/metadata/latest_hashes.json"
    previous_hashes = load_json(latest_hashes_path) if os.path.exists(latest_hashes_path) else {}
    source_changes = diff_hashes(previous_hashes, hashes)

    latest_dataset_path = "data/metadata/latest_dataset.json"
    previous_dataset = load_json(latest_dataset_path) if os.path.exists(latest_dataset_path) else {}
    added, removed, changed = diff_rows(previous_dataset, current_rows)

    save_json(latest_hashes_path, hashes)
    save_json(latest_dataset_path, current_rows)

    snapshot_hashes_path = os.path.join("data/metadata", f"hashes_{run_id}.json")
    snapshot_dataset_path = os.path.join("data/metadata", f"dataset_{run_id}.json")
    save_json(snapshot_hashes_path, hashes)
    save_json(snapshot_dataset_path, current_rows)

    history_line = {
        "run_id": run_id,
        "executed_at_utc": now_iso,
        "source_hashes": hashes,
        "source_changes": source_changes,
        "rows": len(rows),
        "added": len(added),
        "removed": len(removed),
        "changed": len(changed),
    }
    with open("data/metadata/hash_history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(history_line, ensure_ascii=False) + "\n")

    report_path = os.path.join("data/reports", f"delta_{run_id}.md")
    write_report(report_path, now_iso, source_changes, added, removed, changed)
    shutil.copyfile(report_path, "data/reports/last_delta.md")

    print(f"✓ CSV generado: pokeMAP.csv ({len(rows)} filas)")
    if HAS_OPENPYXL:
        print(f"✓ Excel generado: pokeMAP.xlsx")
    else:
        print(f"⚠️  Excel no generado (instala openpyxl: pip install openpyxl)")
    print(f"✓ Hashes guardados en: {latest_hashes_path}")
    print(f"✓ Reporte delta: {report_path}")


if __name__ == "__main__":
    main()
