"""
Script para sincronizar las descripciones oficiales en español de Pokémon Oro HeartGold
desde la API de WikiDex, preservando la variante canónica oficial de los cartuchos en España.
Genera: tracker/data/cache/wikidex_heartgold_descriptions.json
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
    "oro heartgold",
    "oro-heartgold",
    "heartgold",
    "hg",
    "oro"
]

FALLBACK_KEYS = [
    "plata soulsilver",
    "plata-soulsilver",
    "soulsilver",
    "ss",
    "cristal",
    "oro",
    "plata",
    "platino",
    "diamante",
    "perla"
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
    print("Iniciando sincronización oficial de descripciones de Pokémon Oro HeartGold...")

    species_file = CACHE_DIR / "pokemon_493_species.json"
    if not species_file.exists():
        print(f"ERROR: No se encontró {species_file}")
        return

    with open(species_file, "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    cache_output = CACHE_DIR / "wikidex_heartgold_descriptions.json"
    descriptions = {}
    if cache_output.exists() and not force_all:
        try:
            with open(cache_output, "r", encoding="utf-8") as f:
                descriptions = json.load(f)
            print(f"Caché previa encontrada con {len(descriptions)} descripciones.")
        except Exception:
            descriptions = {}

    to_fetch = []
    title_to_id = {}
    for nat_id in range(1, 494):
        s_id = str(nat_id)
        if s_id not in descriptions or not descriptions[s_id] or force_all:
            raw_name = species_493.get(s_id, {}).get("name", "")
            title = CUSTOM_TITLES.get(nat_id, raw_name.capitalize())
            to_fetch.append(title)
            title_to_id[title.lower()] = nat_id

    if not to_fetch:
        print("Todas las descripciones ya están descargadas en caché.")
        return

    print(f"Se descargarán descripciones para {len(to_fetch)} especies en lotes de 40...")
    batch_size = 40
    for i in range(0, len(to_fetch), batch_size):
        batch = to_fetch[i:i+batch_size]
        print(f"Procesando lote {i//batch_size + 1}/{(len(to_fetch)-1)//batch_size + 1}...")
        try:
            res = fetch_wikidex_batch(batch)
            query_res = res.get("query", {})
            normalized = {item["to"]: item["from"] for item in query_res.get("normalized", [])}
            redirects = {item["to"]: item["from"] for item in query_res.get("redirects", [])}
            pages = query_res.get("pages", {})

            for page_id, page in pages.items():
                title = page.get("title", "")
                orig_title = redirects.get(title, title)
                orig_title = normalized.get(orig_title, orig_title)
                nat_id = title_to_id.get(orig_title.lower()) or title_to_id.get(title.lower())

                if not nat_id:
                    continue

                revisions = page.get("revisions", [])
                if not revisions:
                    continue

                slots = revisions[0].get("slots", {})
                main_slot = slots.get("main", {})
                content = main_slot.get("*", "")

                tpl = extract_pokedex_template(content)
                if not tpl:
                    continue

                fields = parse_template_fields(tpl)

                text = ""
                for pk in PRIMARY_KEYS:
                    if pk in fields:
                        text = resolve_field_text(fields, pk)
                        if text:
                            break

                if not text:
                    for fk in FALLBACK_KEYS:
                        if fk in fields:
                            text = resolve_field_text(fields, fk)
                            if text:
                                break

                if text:
                    descriptions[str(nat_id)] = text

        except Exception as e:
            print(f"Error procesando lote: {e}")

    with open(cache_output, "w", encoding="utf-8") as f:
        json.dump(descriptions, f, indent=2, ensure_ascii=False)

    print(f"Sincronización completada: {len(descriptions)} descripciones oficiales en {cache_output}")


if __name__ == "__main__":
    main()
