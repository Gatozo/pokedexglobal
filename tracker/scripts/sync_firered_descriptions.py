"""
Script para sincronizar las descripciones oficiales en español de Pokémon Rojo Fuego
desde la API de WikiDex, preservando la variante oficial de España.
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"

CUSTOM_TITLES = {
    29: "Nidoran hembra",
    32: "Nidoran macho",
    83: "Farfetch'd",
    122: "Mr. Mime",
    233: "Porygon2",
    250: "Ho-Oh",
    386: "Deoxys"
}

PRIMARY_KEYS = [
    "rojo fuego",
    "rojofuego",
    "rf"
]

FALLBACK_KEYS = [
    "verde hoja",
    "verdehoja",
    "vh",
    "esmeralda",
    "rubí",
    "rubi",
    "zafiro",
    "rubí omega",
    "rubi omega",
    "zafiro alfa",
    "diamante",
    "perla",
    "platino",
    "oro heartgold",
    "plata soulsilver"
]


def clean_wiki_text(text: str) -> str:
    """Limpia plantillas, enlaces y formato de WikiDex preservando la variante de España."""
    if not text:
        return ""
    # Plantilla {{NombreHaEs|Texto España|Texto Hispanoamérica}}
    text = re.sub(r'\{\{NombreHaEs\|(.*?)\|(.*?)\}\}', r'\1', text, flags=re.DOTALL)
    # Enlaces [[Destino|Texto visible]] o [[Texto]]
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    # Plantillas residuales {{...}}
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Etiquetas HTML <...>
    text = re.sub(r'<[^>]+>', '', text)
    # Espacios en blanco repetidos
    return " ".join(text.split()).strip()


def resolve_field_text(fields: dict, key: str, depth: int = 0) -> str:
    """Resuelve recursivamente un campo de WikiDex que pueda apuntar a otra versión."""
    if depth > 5 or key not in fields:
        return ""
    val = fields[key].strip()
    if not val or val.lower() == "no hay":
        return ""
    # Si el valor es una referencia a otra clave (ej: "rojo fuego = verde hoja" o "rojo fuego = rubí")
    clean_target = val.lower().replace(" ", "").replace("_", "")
    for k in fields:
        if k.replace(" ", "").replace("_", "") == clean_target:
            return resolve_field_text(fields, k, depth + 1)
    return clean_wiki_text(val)


def main():
    print("Iniciando extracción 100% canónica de descripciones para Pokémon Rojo Fuego...")
    species_file = CACHE_DIR / "pokemon_386_species.json"
    with open(species_file, "r", encoding="utf-8") as f:
        species_386 = json.load(f)

    cache_output = CACHE_DIR / "wikidex_firered_descriptions.json"
    descriptions = {}
    if cache_output.exists():
        with open(cache_output, "r", encoding="utf-8") as f:
            descriptions = json.load(f)

    title_to_nat = {}
    items = []
    for k, v in species_386.items():
        nat_id = int(k)
        if str(nat_id) in descriptions and descriptions[str(nat_id)]:
            continue
        name = v["name"]
        title = CUSTOM_TITLES.get(nat_id, name.capitalize())
        title_to_nat[title.lower()] = nat_id
        items.append((nat_id, title))

    print(f"Especies pendientes por extraer: {len(items)}")
    batch_size = 20
    total_batches = (len(items) + batch_size - 1) // batch_size

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        titles_str = "|".join([b[1] for b in batch])
        url = (
            f"https://www.wikidex.net/api.php?action=query&prop=revisions&redirects=1"
            f"&titles={urllib.parse.quote(titles_str)}&rvprop=content&format=json"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PokedexGlobal/1.0 (Collector Tool; Educational)"}
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Mapeo de redirecciones
            redirects = {r["to"].lower(): r["from"].lower() for r in data.get("query", {}).get("redirects", [])}
            pages = data.get("query", {}).get("pages", {})

            for page_id, page in pages.items():
                title = page.get("title", "")
                orig_title = redirects.get(title.lower(), title.lower())
                nat_id = title_to_nat.get(title.lower()) or title_to_nat.get(orig_title)
                if not nat_id:
                    for b_nat, b_title in batch:
                        if b_title.lower() == title.lower() or b_title.lower() == orig_title:
                            nat_id = b_nat
                            break
                if not nat_id:
                    continue

                content = page.get("revisions", [{}])[0].get("*", "") if page.get("revisions") else ""
                m = re.search(r'\{\{Pokédex(.*?)\}\}', content, re.DOTALL | re.IGNORECASE)
                if not m:
                    continue

                tpl = m.group(1)
                fields = {}
                for line in tpl.split("\n"):
                    line = line.strip()
                    if line.startswith("|"):
                        parts = line[1:].split("=", 1)
                        if len(parts) == 2:
                            k_field = parts[0].strip().lower()
                            v_field = parts[1].strip()
                            fields[k_field] = v_field

                desc_text = ""
                for pk_key in PRIMARY_KEYS:
                    if pk_key in fields:
                        candidate = resolve_field_text(fields, pk_key)
                        if candidate and candidate.lower() != "no hay":
                            desc_text = candidate
                            break

                if not desc_text:
                    for fb_key in FALLBACK_KEYS:
                        if fb_key in fields:
                            candidate = resolve_field_text(fields, fb_key)
                            if candidate and candidate.lower() != "no hay":
                                desc_text = candidate
                                break

                if desc_text:
                    descriptions[str(nat_id)] = desc_text

            print(f"Lote {i // batch_size + 1}/{total_batches} procesado ({len(descriptions)} descripciones totales)...")
        except Exception as e:
            print(f"Error procesando lote {i // batch_size + 1}: {e}")

    with open(cache_output, "w", encoding="utf-8") as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Se han guardado {len(descriptions)} descripciones en {cache_output}")


if __name__ == "__main__":
    main()
