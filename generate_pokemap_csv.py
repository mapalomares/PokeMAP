#!/usr/bin/env python3
import csv
import json
import os
import subprocess
from datetime import datetime


def download_with_curl(url, output_path):
    subprocess.run(
        ["curl", "-fsSL", url, "-o", output_path],
        check=True,
    )


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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


def fetch_level_from_pokeapi(pid):
    tmp_path = f"tmp/species_{pid}.json"
    url = f"https://pokeapi.co/api/v2/pokemon-species/{pid}"
    try:
        download_with_curl(url, tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("is_mythical"):
            return "singular"
        if data.get("is_legendary"):
            return "legendario"
        return "normal"
    except Exception:
        return "desconocido"


def pick_preferred_form(rows):
    by_id = {}
    for row in rows:
        pid = int(row["pokemon_id"])
        current = by_id.get(pid)
        if current is None or row.get("form") == "Normal":
            by_id[pid] = row
    return by_id


def main():
    os.makedirs("tmp", exist_ok=True)

    stats_path = "tmp/pokemon_stats.json"
    types_path = "tmp/pokemon_types.json"
    released_path = "tmp/released_pokemon.json"
    species_path = "tmp/pokemon_species.csv"

    download_with_curl("https://pogoapi.net/api/v1/pokemon_stats.json", stats_path)
    download_with_curl("https://pogoapi.net/api/v1/pokemon_types.json", types_path)
    download_with_curl("https://pogoapi.net/api/v1/released_pokemon.json", released_path)
    download_with_curl(
        "https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species.csv",
        species_path,
    )

    stats = load_json(stats_path)
    types = load_json(types_path)
    released = load_json(released_path)
    levels_by_id = load_species_levels(species_path)

    stats_by_id = pick_preferred_form(stats)
    types_by_id = pick_preferred_form(types)

    type_es = {
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

    fecha = datetime.now().strftime("%Y-%m-%d")
    rows = []

    for pid_str, released_info in released.items():
        pid = int(pid_str)
        st = stats_by_id.get(pid)
        tp = types_by_id.get(pid)
        if st is None:
            continue

        nivel = levels_by_id.get(pid)
        if nivel is None:
            nivel = fetch_level_from_pokeapi(pid)

        tipo_raw = tp.get("type", []) if tp else []
        tipo = "/".join(type_es.get(t, t.lower()) for t in tipo_raw) if tipo_raw else "desconocido"

        nombre = st.get("pokemon_name") or released_info.get("name") or f"Pokemon {pid}"

        rows.append(
            {
                "Nombre": nombre,
                "Tipo": tipo,
                "Nivel": nivel,
                "Ataque Base": st.get("base_attack", ""),
                "Defensa Base": st.get("base_defense", ""),
                "Stamina Base": st.get("base_stamina", ""),
                "fechaActualización": fecha,
            }
        )

    rows.sort(key=lambda r: r["Nombre"].lower())

    with open("pokeMAP.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Nombre",
                "Tipo",
                "Nivel",
                "Ataque Base",
                "Defensa Base",
                "Stamina Base",
                "fechaActualización",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generado pokeMAP.csv con {len(rows)} filas")


if __name__ == "__main__":
    main()
