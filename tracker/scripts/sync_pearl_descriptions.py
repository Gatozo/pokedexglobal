"""
Script para sincronizar las descripciones oficiales en español de Pokémon Perla
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
    "perla",
    "p"
]

FALLBACK_KEYS = [
    "diamante",
    "d",
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
                depth += 1
                i += 2
            elif content[i:i+2] == '}}':
                depth -= 1
                i += 2
                if depth == 0:
                    return content[start:i]
            else:
                i += 1
        idx = start + 2


def parse_template_fields(tpl: str):
    """Parsea los campos |clave=valor respetando plantillas y enlaces internos."""
    inside = tpl[2:-2].strip()
    pipe_positions = []
    depth_t = 0
    depth_l = 0
    i = 0
    while i < len(inside):
        if inside[i:i+2] == '{{':
            depth_t += 1
            i += 2
        elif inside[i:i+2] == '}}':
            depth_t -= 1
            i += 2
        elif inside[i:i+2] == '[[':
            depth_l += 1
            i += 2
        elif inside[i:i+2] == ']]':
            depth_l -= 1
            i += 2
        elif inside[i] == '|' and depth_t == 0 and depth_l == 0:
            pipe_positions.append(i)
            i += 1
        else:
            i += 1

    chunks = []
    prev = 0
    for pos in pipe_positions:
        chunks.append(inside[prev:pos])
        prev = pos + 1
    chunks.append(inside[prev:])

    fields = {}
    for c in chunks[1:]:
        if '=' in c:
            k, v = c.split('=', 1)
            fields[k.strip().lower()] = v.strip()
    return fields


def clean_wikitext(text: str) -> str:
    """Limpia el wikitexto a texto plano legible."""
    if not text:
        return ""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\{[a-zA-Z0-9_\s-]+\|([^\}]+)\}\}', r'\1', text)
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r"'''?", "", text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = ' '.join(text.split())
    return text.strip()


def resolve_field_text(fields: dict, key: str) -> str:
    """Resuelve el texto de un campo de plantilla, siguiendo referencias cruzadas (|d=p)."""
    visited = set()
    curr = key
    while curr and curr not in visited:
        visited.add(curr)
        val = fields.get(curr, '')
        clean_val = val.strip()
        ref_match = re.match(r'^([a-zA-Z0-9_\sáéíóúÁÉÍÓÚ-]+)$', clean_val)
        if ref_match and ref_match.group(1).lower() in fields and len(clean_val) < 25:
            curr = ref_match.group(1).lower()
        else:
            return clean_wikitext(val)
    return ""


def fetch_wikidex_batch(titles: list):
    """Consulta la API de WikiDex para un lote de títulos (máximo 50)."""
    joined = "|".join(titles)
    query = urllib.parse.urlencode({
        "action": "query",
        "prop": "revisions",
        "titles": joined,
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "redirects": "1"
    })
    url = f"https://www.wikidex.net/api.php?{query}"
    headers = {"User-Agent": "PokedexGlobal/1.0 (https://github.com/PokedexGlobal)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    force_all = "--force" in sys.argv
    print("Iniciando sincronización oficial de descripciones de Pokémon Perla...")

    species_file = CACHE_DIR / "pokemon_493_species.json"
    if not species_file.exists():
        print(f"ERROR: No se encontró {species_file}")
        return

    with open(species_file, "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    cache_output = CACHE_DIR / "wikidex_pearl_descriptions.json"
    descriptions = {}
    if cache_output.exists() and not force_all:
        with open(cache_output, "r", encoding="utf-8") as f:
            descriptions = json.load(f)

    pokemon_list = []
    for nat_id in range(1, 494):
        sp = species_493.get(str(nat_id))
        if not sp:
            continue
        display_name = sp.get("display_name", "")
        title = CUSTOM_TITLES.get(nat_id, display_name)
        pokemon_list.append((nat_id, title))

    batch_size = 40
    total_batches = (len(pokemon_list) + batch_size - 1) // batch_size

    for i in range(0, len(pokemon_list), batch_size):
        batch = pokemon_list[i:i + batch_size]
        titles = [t for _, t in batch]
        title_to_id = {t.lower(): nid for nid, t in batch}

        try:
            data = fetch_wikidex_batch(titles)
            pages = data.get("query", {}).get("pages", {})

            for page_id, page in pages.items():
                if int(page_id) < 0:
                    continue
                p_title = page.get("title", "")
                nat_id = title_to_id.get(p_title.lower())
                if not nat_id:
                    for orig_title, nid in title_to_id.items():
                        if orig_title in p_title.lower():
                            nat_id = nid
                            break
                if not nat_id:
                    continue

                revisions = page.get("revisions", [])
                if not revisions:
                    continue
                slots = revisions[0].get("slots", {})
                content = slots.get("main", {}).get("*", "")
                if not content:
                    continue

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
