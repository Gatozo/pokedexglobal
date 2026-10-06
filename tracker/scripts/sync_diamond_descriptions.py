"""
Script para sincronizar las descripciones oficiales en español de Pokémon Diamante
desde la API de WikiDex, preservando la variante canónica oficial de los cartuchos en España.
"""
import json
import re
import sys
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
    386: "Deoxys",
    413: "Wormadam",
    439: "Mime Jr.",
    474: "Porygon-Z",
    487: "Giratina",
    492: "Shaymin"
}

PRIMARY_KEYS = [
    "diamante",
    "d"
]

FALLBACK_KEYS = [
    "perla",
    "p",
    "platino",
    "pt",
    "oro heartgold",
    "plata soulsilver",
    "esmeralda",
    "rojo fuego",
    "verde hoja",
    "rubí",
    "zafiro"
]


def extract_pokedex_template(content: str):
    """Extrae el bloque {{Pokédex ...}} respetando llaves anidadas de forma estricta."""
    idx = 0
    while True:
        m = re.search(r'\{\{pok[ée]dex\b', content[idx:], re.IGNORECASE)
        if not m:
            return None
        start = idx + m.start()
        depth = 0
        i = start
        while i < len(content):
            if content[i:i+2] == '{{':
                depth += 2
                i += 2
            elif content[i:i+2] == '}}':
                depth -= 2
                i += 2
                if depth == 0:
                    return content[start:i]
            else:
                i += 1
        idx = start + 2
    return None


def parse_template_fields(tpl: str):
    """Parsea los campos de nivel superior de la plantilla {{Pokédex ...}}."""
    if not tpl:
        return {}
    m = re.match(r'\{\{pok[ée]dex\s*(.*?)\}\}$', tpl, re.DOTALL | re.IGNORECASE)
    if not m:
        return {}
    body = m.group(1)
    fields = {}
    current_key = None
    current_val = []
    i = 0
    depth = 0
    while i < len(body):
        if body[i:i+2] in ('{{', '[['):
            depth += 2
            current_val.append(body[i:i+2])
            i += 2
        elif body[i:i+2] in ('}}', ']]'):
            depth -= 2
            current_val.append(body[i:i+2])
            i += 2
        elif body[i] == '|' and depth == 0:
            if current_key is not None:
                fields[current_key] = ''.join(current_val).strip()
            rest = body[i+1:]
            eq_idx = -1
            j = 0
            d = 0
            while j < len(rest):
                if rest[j:j+2] in ('{{', '[['): d += 2; j += 2
                elif rest[j:j+2] in ('}}', ']]'): d -= 2; j += 2
                elif rest[j] == '=' and d == 0: eq_idx = j; break
                elif rest[j] == '|' and d == 0: break
                else: j += 1
            if eq_idx != -1:
                current_key = rest[:eq_idx].strip().lower()
                current_val = []
                i = i + 1 + eq_idx + 1
            else:
                current_key = None
                current_val = []
                i += 1
        else:
            if current_key is not None:
                current_val.append(body[i])
            i += 1
    if current_key is not None:
        fields[current_key] = ''.join(current_val).strip()
    return fields


def clean_wiki_text(text: str) -> str:
    """Limpia plantillas, enlaces y formato de WikiDex preservando la variante oficial de España."""
    if not text:
        return ""
    # En WikiDex: {{NombreHaEs|Texto Hispanoamérica|Texto España}} o {{n|...}}
    text = re.sub(r'\{\{(?:NombreHaEs|n)\|([^|]+)(?:\|([^}]+))?\}*', lambda m: m.group(2) or m.group(1), text)
    # Enlaces [[Destino|Texto visible]] o [[Texto]]
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    # Plantillas residuales {{...}}
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Referencias y etiquetas HTML <...>
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    # Espacios y saltos de línea repetidos
    return " ".join(text.split()).strip()


def resolve_field_text(fields: dict, key: str, depth: int = 0) -> str:
    """Resuelve recursivamente un campo de WikiDex que pueda apuntar a otra versión."""
    if depth > 5 or key not in fields:
        return ""
    val = fields[key].strip()
    if not val or val.lower() == "no hay":
        return ""
    clean_target = val.lower().replace(" ", "").replace("_", "")
    for k in fields:
        if k.replace(" ", "").replace("_", "") == clean_target:
            return resolve_field_text(fields, k, depth + 1)
    return clean_wiki_text(val)


def main():
    force_all = "--force" in sys.argv or "-f" in sys.argv
    print("Iniciando extracción y verificación canónica de descripciones para Pokémon Diamante...")
    species_file = CACHE_DIR / "pokemon_493_species.json"
    with open(species_file, "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    cache_output = CACHE_DIR / "wikidex_diamond_descriptions.json"
    descriptions = {}
    if cache_output.exists() and not force_all:
        with open(cache_output, "r", encoding="utf-8") as f:
            descriptions = json.load(f)

    title_to_nat = {}
    items = []
    for k, v in species_493.items():
        nat_id = int(k)
        if not force_all and str(nat_id) in descriptions and descriptions[str(nat_id)]:
            continue
        name = v["name"]
        title = CUSTOM_TITLES.get(nat_id, name.capitalize())
        title_to_nat[title.lower()] = nat_id
        items.append((nat_id, title))

    print(f"Especies a sincronizar/verificar: {len(items)}")
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
                tpl = extract_pokedex_template(content)
                if not tpl:
                    continue

                fields = parse_template_fields(tpl)

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

    print(f"\n[OK] Se han guardado y verificado {len(descriptions)} descripciones oficiales en {cache_output}")


if __name__ == "__main__":
    main()
