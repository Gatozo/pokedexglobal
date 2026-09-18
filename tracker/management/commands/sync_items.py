import os
import csv
import io
import json
import requests
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Set
from django.conf import settings
from django.core.management.base import BaseCommand

# URLs para los recursos de PokeAPI en GitHub
SPRITES_TREE_URL = "https://api.github.com/repos/PokeAPI/sprites/git/trees/master?recursive=1"
SPRITES_RAW_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/"

CSV_BASE_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/"

DATA_DIR = settings.BASE_DIR / "tracker" / "data"
ITEMS_JSON_PATH = DATA_DIR / "items.json"


def fetch_csv(session: requests.Session, filename: str) -> List[Dict[str, str]]:
    """Descarga y parsea un archivo CSV oficial de PokeAPI desde GitHub."""
    url = f"{CSV_BASE_URL}{filename}"
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    content = resp.content.decode("utf-8")
    return list(csv.DictReader(io.StringIO(content)))


class Command(BaseCommand):
    help = "Descarga y almacena localmente todos los sprites de objetos (Poké Balls, pociones, fósiles, etc.) y su catálogo completo con nombres y descripciones en español."

    def add_arguments(self, parser):
        parser.add_argument(
            "--workers",
            type=int,
            default=24,
            help="Número de hilos concurrentes para descarga de imágenes (por defecto: 24)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Fuerza la re-descarga de archivos aunque ya existan localmente"
        )
        parser.add_argument(
            "--skip-sprites",
            action="store_true",
            help="Omite la descarga de sprites y solo genera el catálogo items.json"
        )
        parser.add_argument(
            "--skip-metadata",
            action="store_true",
            help="Omite la generación del catálogo de metadatos y solo descarga los sprites"
        )

    def download_file(self, session: requests.Session, url: str, target_path: Path, force: bool = False) -> bool:
        if target_path.exists() and not force and target_path.stat().st_size > 0:
            return False

        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 0:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception:
            pass
        return False

    def handle(self, *args, **options):
        workers = options["workers"]
        force = options["force"]
        skip_sprites = options["skip_sprites"]
        skip_metadata = options["skip_metadata"]

        media_items_dir = settings.MEDIA_ROOT / "items"
        media_items_dir.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (PokedexGlobal)"})

        available_sprites: Set[str] = set()

        # 1. DESCARGA DE SPRITES DE OBJETOS
        if not skip_sprites:
            self.stdout.write("Consultando árbol completo de sprites de objetos en PokeAPI...")
            try:
                tree_resp = session.get(SPRITES_TREE_URL, timeout=20)
                if tree_resp.status_code != 200:
                    self.stderr.write(f"Error al conectar con GitHub API: HTTP {tree_resp.status_code}")
                    return
                tree_data = tree_resp.json()
            except Exception as e:
                self.stderr.write(f"Excepción al conectar con GitHub: {e}")
                return

            item_files = [
                t["path"] for t in tree_data.get("tree", [])
                if t["path"].startswith("sprites/items/") and t["path"].endswith(".png")
            ]
            self.stdout.write(f"Se identificaron {len(item_files)} sprites de objetos en PokeAPI.")

            tasks = []
            for path in item_files:
                rel_path = path.replace("sprites/items/", "")
                target_path = media_items_dir / rel_path
                raw_url = f"{SPRITES_RAW_BASE}{path}"
                tasks.append((raw_url, target_path, rel_path))
                available_sprites.add(rel_path)

            self.stdout.write(f"Iniciando descarga concurrente con {workers} hilos...")
            downloaded = 0
            skipped = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self.download_file, session, url, path, force): rel
                    for url, path, rel in tasks
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        res = future.result()
                        if res:
                            downloaded += 1
                        else:
                            skipped += 1
                    except Exception:
                        pass

            self.stdout.write(self.style.SUCCESS(
                f"Descarga de sprites completada: {downloaded} nuevos/actualizados, {skipped} ya existentes."
            ))
        else:
            for p in media_items_dir.rglob("*.png"):
                available_sprites.add(p.relative_to(media_items_dir).as_posix())

        # 2. PROCESAMIENTO Y GENERACIÓN DEL CATÁLOGO DE METADATOS (ITEMS.JSON)
        if not skip_metadata:
            self.stdout.write("Descargando metadatos canónicos de PokeAPI (nombres, categorías, bolsillos y descripciones en español)...")
            try:
                items_csv = fetch_csv(session, "items.csv")
                names_csv = fetch_csv(session, "item_names.csv")
                categories_csv = fetch_csv(session, "item_categories.csv")
                pockets_csv = fetch_csv(session, "item_pockets.csv")
                pocket_names_csv = fetch_csv(session, "item_pocket_names.csv")
                flavor_csv = fetch_csv(session, "item_flavor_text.csv")
            except Exception as e:
                self.stderr.write(f"Error al descargar datasets CSV de PokeAPI: {e}")
                return

            # Mapear nombres de bolsillos (pockets): id -> {es, en, slug}
            pockets_map = {p["id"]: {"slug": p["identifier"], "name_es": "", "name_en": ""} for p in pockets_csv}
            for pn in pocket_names_csv:
                pid = pn["item_pocket_id"]
                if pid in pockets_map:
                    if pn["local_language_id"] == "7":
                        pockets_map[pid]["name_es"] = pn["name"]
                    elif pn["local_language_id"] == "9":
                        pockets_map[pid]["name_en"] = pn["name"]

            # Mapear categorías: id -> {slug, pocket_id}
            categories_map = {c["id"]: {"slug": c["identifier"], "pocket_id": c["pocket_id"]} for c in categories_csv}

            # Mapear nombres de objetos: item_id -> {es, en}
            names_map: Dict[str, Dict[str, str]] = {}
            for row in names_csv:
                iid = row["item_id"]
                lang = row["local_language_id"]
                if iid not in names_map:
                    names_map[iid] = {"es": "", "en": ""}
                if lang == "7":
                    names_map[iid]["es"] = row["name"]
                elif lang == "9":
                    names_map[iid]["en"] = row["name"]

            # Mapear textos de descripción (flavor text) más recientes: item_id -> {es, en}
            flavor_map: Dict[str, Dict[str, Any]] = {}
            for row in flavor_csv:
                iid = row["item_id"]
                lang = row["language_id"]
                vg_id = int(row.get("version_group_id", 0) or 0)
                text = row["flavor_text"].replace("\n", " ").replace("\x0c", " ").strip()

                if iid not in flavor_map:
                    flavor_map[iid] = {"es": "", "es_vg": -1, "en": "", "en_vg": -1}

                if lang == "7" and vg_id >= flavor_map[iid]["es_vg"]:
                    flavor_map[iid]["es"] = text
                    flavor_map[iid]["es_vg"] = vg_id
                elif lang == "9" and vg_id >= flavor_map[iid]["en_vg"]:
                    flavor_map[iid]["en"] = text
                    flavor_map[iid]["en_vg"] = vg_id

            # Consolidar catálogo de objetos indexado por slug y por ID
            catalog: Dict[str, Any] = {}
            by_id: Dict[int, str] = {}

            for row in items_csv:
                item_id = int(row["id"])
                slug = row["identifier"]
                cat_info = categories_map.get(row.get("category_id", ""), {})
                cat_slug = cat_info.get("slug", "other")
                pocket_id = cat_info.get("pocket_id", "")
                pocket_info = pockets_map.get(pocket_id, {"slug": "misc", "name_es": "Objetos", "name_en": "Items"})

                item_names = names_map.get(row["id"], {})
                name_en = item_names.get("en") or slug.replace("-", " ").title()
                name_es = item_names.get("es") or name_en

                flavors = flavor_map.get(row["id"], {})
                desc_es = flavors.get("es", "")
                desc_en = flavors.get("en", "")

                cost = int(row.get("cost", 0) or 0)

                canonical_rel = f"{slug}.png"
                has_canonical = canonical_rel in available_sprites or (media_items_dir / canonical_rel).exists()

                sub_sprites = {}
                for folder in ["dream-world", "berries", "underground", "gen5", "gen8", "gen9"]:
                    sub_rel = f"{folder}/{slug}.png"
                    if sub_rel in available_sprites or (media_items_dir / folder / f"{slug}.png").exists():
                        sub_sprites[folder] = f"{settings.MEDIA_URL}items/{sub_rel}"

                entry = {
                    "id": item_id,
                    "slug": slug,
                    "name": name_en,
                    "name_es": name_es,
                    "category": cat_slug,
                    "pocket": pocket_info["slug"],
                    "pocket_name_es": pocket_info["name_es"],
                    "cost": cost,
                    "flavor_text_es": desc_es,
                    "flavor_text_en": desc_en,
                    "has_sprite": has_canonical,
                    "sprite_url": f"{settings.MEDIA_URL}items/{canonical_rel}" if has_canonical else None,
                    "subfolder_sprites": sub_sprites
                }

                catalog[slug] = entry
                by_id[item_id] = slug

            with open(ITEMS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "meta": {
                        "total_items": len(catalog),
                        "items_with_sprites": sum(1 for v in catalog.values() if v["has_sprite"]),
                    },
                    "items": catalog,
                    "by_id": by_id,
                }, f, ensure_ascii=False, indent=2)

            self.stdout.write(self.style.SUCCESS(
                f"Catálogo items.json generado exitosamente en {ITEMS_JSON_PATH} ({len(catalog)} objetos procesados)."
            ))
