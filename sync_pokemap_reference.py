#!/usr/bin/env python3
import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone


SOURCES = {
    "pokemon_stats": "https://pogoapi.net/api/v1/pokemon_stats.json",
    "pokemon_types": "https://pogoapi.net/api/v1/pokemon_types.json",
    "released_pokemon": "https://pogoapi.net/api/v1/released_pokemon.json",
    "pokemon_species_csv": "https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species.csv",
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


def load_species_levels(path):
    levels = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                pid = int(row["id"])
            except Exception:
                continue
            is_legendary = row.get("is_legendary", "0") == "1"
            is_mythical = row.get("is_mythical", "0") == "1"
            if is_mythical:
                levels[pid] = "singular"
            elif is_legendary:
                levels[pid] = "legendario"
            else:
                levels[pid] = "normal"
    return levels


def pick_preferred_form(rows):
    by_id = {}
    for row in rows:
        pid = int(row["pokemon_id"])
        current = by_id.get(pid)
        if current is None or row.get("form") == "Normal":
            by_id[pid] = row
    return by_id


def build_rows(stats, types, released, levels_by_id):
    stats_by_id = pick_preferred_form(stats)
    types_by_id = pick_preferred_form(types)
    fecha = datetime.now().strftime("%Y-%m-%d")
    rows = []

    for pid_str, released_info in released.items():
        pid = int(pid_str)
        st = stats_by_id.get(pid)
        tp = types_by_id.get(pid)
        if st is None:
            continue

        nivel = levels_by_id.get(pid, "desconocido")
        tipo_raw = tp.get("type", []) if tp else []
        tipo = "/".join(TYPE_ES.get(t, t.lower()) for t in tipo_raw) if tipo_raw else "desconocido"
        nombre = st.get("pokemon_name") or released_info.get("name") or f"Pokemon {pid}"

        rows.append(
            {
                "id": pid,
                "Nombre": nombre,
                "Tipo": tipo,
                "Nivel": nivel,
                "Ataque Base": st.get("base_attack", ""),
                "Defensa Base": st.get("base_defense", ""),
                "Stamina Base": st.get("base_stamina", ""),
                "fechaActualizacion": fecha,
            }
        )

    rows.sort(key=lambda r: (r["id"], r["Nombre"].lower()))
    return rows


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Nombre",
                "Tipo",
                "Nivel",
                "Ataque Base",
                "Defensa Base",
                "Stamina Base",
                "fechaActualizacion",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in writer.fieldnames})


def rows_by_id(rows):
    out = {}
    for row in rows:
        out[str(row["id"])] = {
            "Nombre": row["Nombre"],
            "Tipo": row["Tipo"],
            "Nivel": row["Nivel"],
            "Ataque Base": row["Ataque Base"],
            "Defensa Base": row["Defensa Base"],
            "Stamina Base": row["Stamina Base"],
        }
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
        for field in ["Nombre", "Tipo", "Nivel", "Ataque Base", "Defensa Base", "Stamina Base"]:
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
    levels_by_id = load_species_levels(local_files["pokemon_species_csv"])

    rows = build_rows(stats, types, released, levels_by_id)
    write_csv(rows, "pokeMAP.csv")
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

    print(f"CSV generado: pokeMAP.csv ({len(rows)} filas)")
    print(f"Hashes guardados en: {latest_hashes_path}")
    print(f"Reporte delta: {report_path}")


if __name__ == "__main__":
    main()
