"""
Script para sincronizar las descripciones canónicas oficiales en español de España
para Pokémon Rojo, Azul y Amarillo (Gen 1) desde WikiDex.

Actualiza:
- tracker/data/flavor_texts/red_es.json
- tracker/data/flavor_texts/blue_es.json
- tracker/data/flavor_texts/yellow_es.json
- El campo `flavor_text` en tracker/data/catalogs/{red,blue,yellow}.json
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FLAVOR_DIR = BASE_DIR / "tracker" / "data" / "flavor_texts"
CATALOGS_DIR = BASE_DIR / "tracker" / "data" / "catalogs"

CUSTOM_TITLES = {
    29: "Nidoran hembra",
    32: "Nidoran macho",
    83: "Farfetch'd",
    122: "Mr. Mime",
}


def extract_pokedex_template(content: str) -> str:
    """Extrae el bloque {{Pokédex ...}} respetando llaves anidadas."""
    idx = 0
    while True:
        m = re.search(r"\{\{pok[ée]dex\b", content[idx:], re.IGNORECASE)
        if not m:
            return ""
        start = idx + m.start()
        depth = 0
        i = start
        while i < len(content):
            if content[i:i + 2] == "{{":
                depth += 1
                i += 2
            elif content[i:i + 2] == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    return content[start:i]
            else:
                i += 1
        idx = start + 2


def parse_template_fields(tpl: str) -> dict:
    """Parsea los campos |clave=valor respetando plantillas y enlaces internos."""
    if not tpl:
        return {}
    inside = tpl[2:-2].strip()
    pipe_positions = []
    depth_t = 0
    depth_l = 0
    i = 0
    while i < len(inside):
        if inside[i:i + 2] == "{{":
            depth_t += 1
            i += 2
        elif inside[i:i + 2] == "}}":
            depth_t -= 1
            i += 2
        elif inside[i:i + 2] == "[[":
            depth_l += 1
            i += 2
        elif inside[i:i + 2] == "]]":
            depth_l -= 1
            i += 2
        elif inside[i] == "|" and depth_t == 0 and depth_l == 0:
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
    for chunk in chunks[1:]:
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            k_norm = k.strip().lower()
            if k_norm not in fields:
                fields[k_norm] = v.strip()
    return fields


def clean_wikitext(text: str) -> str:
    """Limpia plantillas y enlaces de WikiDex preservando la variante de España."""
    if not text:
        return ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(
        r"\{\{(?:NombreHaEs|n)\|([^|}]+)(?:\|([^}]+))?\}\}",
        lambda m: m.group(2) or m.group(1),
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\{\{[a-zA-Z0-9_\s-]+\|([^\}]+)\}\}", r"\1", text)
    text = re.sub(r"\{\{[^\}]+\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'''?", "", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return " ".join(text.split()).strip()


def resolve_field(fields: dict, keys: list) -> str:
    """Resuelve el texto para la primera clave válida de la plantilla."""
    for key in keys:
        if key not in fields:
            continue
        visited = set()
        curr = key
        while curr and curr not in visited:
            visited.add(curr)
            val = fields.get(curr, "").strip()
            if not val or val.lower() == "no hay":
                break
            if val.lower() in fields and len(val) < 25:
                curr = val.lower()
                continue
            return clean_wikitext(val)
    return ""


def fetch_wikidex_batch(titles: list) -> dict:
    """Consulta un lote de artículos en la API de WikiDex."""
    query = urllib.parse.urlencode({
        "action": "query",
        "prop": "revisions",
        "titles": "|".join(titles),
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "redirects": "1",
    })
    url = f"https://www.wikidex.net/api.php?{query}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PokedexGlobal/1.0 (Collector Tool; Educational)"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("Iniciando sincronización canónica en español de Gen 1 (Rojo, Azul, Amarillo)...")

    red_catalog_path = CATALOGS_DIR / "red.json"
    with open(red_catalog_path, "r", encoding="utf-8") as f:
        red_catalog = json.load(f)

    species_list = [
        (
            entry["pokemon"]["national_number"],
            entry["pokemon"]["name"],
            CUSTOM_TITLES.get(entry["pokemon"]["national_number"], entry["pokemon"]["display_name"]),
        )
        for entry in red_catalog
    ]

    fields_by_nat = {}
    batch_size = 40
    for i in range(0, len(species_list), batch_size):
        batch = species_list[i:i + batch_size]
        title_to_nat = {title.lower(): nat for nat, _, title in batch}
        res = fetch_wikidex_batch([t for _, _, t in batch])
        query_data = res.get("query", {})
        normalized = {n["to"].lower(): n["from"].lower() for n in query_data.get("normalized", [])}
        redirects = {r["to"].lower(): r["from"].lower() for r in query_data.get("redirects", [])}

        for page_id, page in query_data.get("pages", {}).items():
            if int(page_id) < 0:
                continue
            pt = page.get("title", "").lower()
            orig = redirects.get(pt, pt)
            orig = normalized.get(orig, orig)
            nat_id = title_to_nat.get(pt) or title_to_nat.get(orig)
            if not nat_id:
                continue
            revs = page.get("revisions", [])
            if not revs:
                continue
            content = revs[0].get("slots", {}).get("main", {}).get("*", "")
            tpl = extract_pokedex_template(content)
            fields_by_nat[nat_id] = parse_template_fields(tpl)

    game_configs = [
        ("red", ["rojoyazul"]),
        ("blue", ["rojoyazul"]),
        ("yellow", ["amarillo"]),
    ]

    for slug, keys in game_configs:
        flavor_path = FLAVOR_DIR / f"{slug}_es.json"
        catalog_path = CATALOGS_DIR / f"{slug}.json"

        with open(flavor_path, "r", encoding="utf-8") as f:
            flavor_data = json.load(f)
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        updated_flavor = 0
        for nat_id, sp_name, _ in species_list:
            text = resolve_field(fields_by_nat.get(nat_id, {}), keys)
            if not text:
                raise RuntimeError(f"No se encontró descripción WikiDex para {slug} #{nat_id} ({sp_name})")
            s_id = str(nat_id)
            if flavor_data.get(s_id, {}).get("flavor_text_es") != text:
                updated_flavor += 1
            flavor_data[s_id] = {"name": sp_name, "flavor_text_es": text}

        updated_catalog = 0
        for entry in catalog_data:
            nid = entry["pokemon"]["national_number"]
            new_text = flavor_data[str(nid)]["flavor_text_es"]
            if entry.get("flavor_text") != new_text:
                entry["flavor_text"] = new_text
                updated_catalog += 1

        with open(flavor_path, "w", encoding="utf-8") as f:
            json.dump(flavor_data, f, ensure_ascii=False, indent=2)
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog_data, f, ensure_ascii=False, indent=2)

        print(f"[OK] {slug}: {updated_flavor} flavor_texts y {updated_catalog} entradas de catálogo actualizadas.")


if __name__ == "__main__":
    main()
