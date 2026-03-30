#!/usr/bin/env python3
"""
check_pokemon.py — Consulta rápida de Pokémon para determinar su utilidad
Uso: python3 check_pokemon.py <nombre_pokemon>
"""
import csv
import sys
from pathlib import Path

# Emojis y utilidades
SCORES_EMOJI = {
    "pve": "⚔️ ",
    "pvp_gl": "🥊 ",
    "pvp_ul": "🥊 ",
    "raid": "🛡️ ",
    "coleccionable": "📦",
}

TIER_EMOJI = {
    "legendario": "👑",
    "singular": "✨",
    "ultraente": "🌀",
    "bebe": "👶",
    "normal": "⭕",
}

NIVEL_EMOJI = {
    "legendario": "👑",
    "singular": "✨",
    "normal": "⚪",
    "desconocido": "❓",
}

SCORE_COLORS = {
    "critical": "\033[91m",  # Rojo
    "high": "\033[92m",      # Verde
    "medium": "\033[93m",    # Amarillo
    "low": "\033[94m",       # Azul
    "none": "\033[97m",      # Blanco
}

RESET = "\033[0m"
BOLD = "\033[1m"


def load_pokemon_data(csv_path="pokeMAP.csv"):
    """Carga todos los Pokémon del CSV."""
    data = {}
    if not Path(csv_path).exists():
        print(f"❌ Error: {csv_path} no encontrado")
        sys.exit(1)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre = row["Nombre"].lower()
            data[nombre] = row

    return data


def find_pokemon(name, data):
    """Busca un Pokémon por nombre (exacto o parcial, case-insensitive)."""
    name_lower = name.lower()

    # Exacto
    if name_lower in data:
        return data[name_lower]

    # Parcial
    matches = [p for p in data.keys() if name_lower in p]
    if len(matches) == 1:
        return data[matches[0]]
    elif len(matches) > 1:
        print(f"\n❓ Se encontraron múltiples coincidencias:")
        for m in matches[:10]:
            print(f"  - {data[m]['Nombre']}")
        if len(matches) > 10:
            print(f"  ... y {len(matches) - 10} más")
        sys.exit(1)
    else:
        print(f"❌ Pokémon '{name}' no encontrado")
        sys.exit(1)


def colorize_score(score):
    """Devuelve score con color según su valor."""
    try:
        s = int(score)
    except (ValueError, TypeError):
        return score

    if s >= 80:
        color = SCORE_COLORS["high"]
        emoji = "🔥"
    elif s >= 60:
        color = SCORE_COLORS["medium"]
        emoji = "⚡"
    elif s >= 40:
        color = SCORE_COLORS["low"]
        emoji = "💤"
    else:
        color = SCORE_COLORS["none"]
        emoji = "❄️"

    return f"{color}{emoji} {s}{RESET}"


def format_etiquetas(etiquetas_str):
    """Formatea etiquetas como tags visuales."""
    if not etiquetas_str:
        return "—"
    etiquetas = etiquetas_str.split(",")
    tags = []
    for e in etiquetas:
        e = e.strip()
        if e == "mega":
            tags.append("💪 Mega")
        elif e == "primigenio":
            tags.append("🌊 Primigenio")
        elif e == "sombra":
            tags.append("👻 Sombra")
        elif e == "regional":
            tags.append("🌍 Regional")
        elif e == "bebe":
            tags.append("👶 Bebé")
    return " | ".join(tags) if tags else "—"


def display_pokemon(pokemon):
    """Muestra la información del Pokémon de forma visual."""
    nombre = pokemon["Nombre"]
    tipo = pokemon["Tipo"]
    nivel_base = pokemon["NivelBase"]
    categoria_go = pokemon["CategoriaGO"]
    etiquetas = pokemon["EtiquetasGO"]
    es_bebe = pokemon["esBebe"]
    region = pokemon["Region"]
    ataque = pokemon["Ataque Base"]
    defensa = pokemon["Defensa Base"]
    stamina = pokemon["Stamina Base"]
    score_pve = pokemon["ScorePvE"]
    score_pvp_gl = pokemon["ScorePvP_GL"]
    score_pvp_ul = pokemon["ScorePvP_UL"]
    uso_principal = pokemon["UsoPrincipal"]
    contadores = pokemon["Contadores"]
    es_raid = pokemon["EsRaid"]
    evoluciona_a = pokemon.get("EvolucionaA", "")
    evolucion_recomendada = pokemon.get("EvolucionRecomendada", "")
    uso_evo_recomendada = pokemon.get("UsoEvolucionRecomendada", "")
    score_evo_recomendada = pokemon.get("ScoreEvolucionRecomendada", "")
    coste_caramelos_evo = pokemon.get("CosteCaramelosEvolucionRecomendada", "")
    objetos_evo = pokemon.get("ObjetosEvolucionRecomendada", "")

    nivel_icon = NIVEL_EMOJI.get(nivel_base, "❓")
    categoria_icon = TIER_EMOJI.get(categoria_go, "⭕")
    uso_icon = SCORES_EMOJI.get(uso_principal, "❓")

    # Header
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}{nivel_icon} {nombre.upper()} {categoria_icon}{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}\n")

    # Clasificación
    print(f"📋 {BOLD}Clasificación{RESET}")
    print(f"   Tipo: {tipo}")
    print(f"   Nivel Base: {nivel_base.capitalize()}")
    print(f"   Categoría GO: {categoria_go.capitalize()}")
    print(f"   Etiquetas: {format_etiquetas(etiquetas)}")
    if region:
        print(f"   Región: {region}")

    # Stats
    print(f"\n💪 {BOLD}Stats Base{RESET}")
    print(f"   Ataque:  {ataque:>3} | Defensa: {defensa:>3} | Stamina: {stamina:>3}")

    # Scores
    print(f"\n📊 {BOLD}Útilidad (Scores){RESET}")
    print(f"   PvE:      {colorize_score(score_pve)} /100")
    print(f"   PvP Gran Liga: {colorize_score(score_pvp_gl)} /100")
    print(f"   PvP Ultra Liga: {colorize_score(score_pvp_ul)} /100")

    # Recomendación
    print(f"\n✅ {BOLD}Recomendación Principal{RESET}")
    uso_texto = {
        "pve": "Excelente para contenido PvE (raids offline)",
        "pvp_gl": "Muy bueno para PvP Gran Liga (CP ≤1500)",
        "pvp_ul": "Excelente para PvP Ultra Liga (CP ≤2500)",
        "raid": "Actualmente en raids (nivel 1)",
        "coleccionable": "Principalmente para colección",
    }
    print(f"   {uso_icon} {BOLD}{uso_texto.get(uso_principal, 'Desconocido').upper()}{RESET}")

    # Evoluciones
    print(f"\n🔁 {BOLD}Potencial de Evolución{RESET}")
    if evoluciona_a:
        print(f"   Evoluciona a: {evoluciona_a}")
    else:
        print(f"   Evoluciona a: —")

    if evolucion_recomendada:
        print(f"   Recomendado: {BOLD}{evolucion_recomendada}{RESET}")
        uso_evo_texto = uso_texto.get(uso_evo_recomendada, uso_evo_recomendada)
        print(f"   Uso recomendado tras evolucionar: {uso_evo_texto}")
        if score_evo_recomendada:
            print(f"   Score potencial (suma PvE+PvP): {score_evo_recomendada}")
        if coste_caramelos_evo:
            print(f"   Coste caramelos: {coste_caramelos_evo}")
        if objetos_evo:
            print(f"   Objeto requerido: {objetos_evo}")
    else:
        print("   Recomendado: mantener actual")

    # Contadores
    if contadores and contadores != "—":
        print(f"\n💥 {BOLD}Es fuerte contra{RESET}")
        print(f"   {contadores}")

    # Estado en raids
    if es_raid == "sí":
        print(f"\n🛡️  {BOLD}¡ESTÁ EN RAIDS AHORA!{RESET}")
    elif es_bebe == "sí":
        print(f"\n👶 {BOLD}Es un Pokémon Bebé (valioso para intercambio){RESET}")

    # Footer
    print(f"\n{BOLD}{'=' * 70}{RESET}\n")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 check_pokemon.py <nombre_pokemon>")
        print("\nEjemplos:")
        print("  python3 check_pokemon.py mewtwo")
        print("  python3 check_pokemon.py blissey")
        print("  python3 check_pokemon.py deino")
        sys.exit(1)

    pokemon_name = " ".join(sys.argv[1:])
    data = load_pokemon_data()
    pokemon = find_pokemon(pokemon_name, data)
    display_pokemon(pokemon)


if __name__ == "__main__":
    main()
