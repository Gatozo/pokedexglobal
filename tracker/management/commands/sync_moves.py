import json
import os
import concurrent.futures
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Move
from tracker.utils import safe_api_get

MAX_MOVE_ID_GEN = {
    1: 165,
    2: 251,
    3: 354,
    4: 467,
    5: 559,
}

MOVES_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "moves_gen1.json"
)

class Command(BaseCommand):
    help = "Descarga y almacena los movimientos completos con estadísticas, daño y español oficial."

    def add_arguments(self, parser):
        parser.add_argument(
            "--generation",
            type=int,
            default=1,
            help="Generación de movimientos a descargar (por defecto: 1, movimientos 1 al 165)"
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=10,
            help="Hilos concurrentes para descarga (por defecto: 10)"
        )
        parser.add_argument(
            "--local",
            action="store_true",
            help="Carga los movimientos desde el archivo local sin conectar a Internet"
        )

    def fetch_move_data(self, move_id: int):
        resp = safe_api_get(f"https://pokeapi.co/api/v2/move/{move_id}/", pacing_delay=0.02)
        if not resp or resp.status_code != 200:
            return None
        data = resp.json()
        
        names = {n["language"]["name"]: n["name"] for n in data.get("names", [])}
        display_name = names.get("es") or names.get("en") or data.get("name", "").replace("-", " ").title()
        
        flavors = [f["flavor_text"].replace("\n", " ").replace("\x0c", " ") for f in data.get("flavor_text_entries", []) if f["language"]["name"] == "es"]
        effect = flavors[-1] if flavors else ""
        if not effect:
            effects = [e["short_effect"] for e in data.get("effect_entries", []) if e["language"]["name"] == "es"]
            effect = effects[0] if effects else ""

        gen_url = data.get("generation", {}).get("url", "")
        gen_num = 1
        if gen_url:
            try:
                gen_num = int(gen_url.rstrip("/").split("/")[-1])
            except (ValueError, IndexError):
                pass

        return {
            "id": data["id"],
            "name": data["name"],
            "display_name": display_name,
            "generation": gen_num,
            "type": data.get("type", {}).get("name", "normal"),
            "power": data.get("power"),
            "accuracy": data.get("accuracy"),
            "pp": data.get("pp") or 0,
            "damage_class": data.get("damage_class", {}).get("name", ""),
            "effect_description": effect,
            "raw_data": data,
        }

    def handle(self, *args, **options):
        gen = options["generation"]
        workers = options["workers"]
        local_only = options["local"]
        max_id = MAX_MOVE_ID_GEN.get(gen, 165)

        if local_only and os.path.exists(MOVES_FILE_PATH):
            self.stdout.write(f"Cargando movimientos de Generación {gen} desde archivo local: {MOVES_FILE_PATH}...")
            with open(MOVES_FILE_PATH, "r", encoding="utf-8") as f:
                moves_list = json.load(f)
        else:
            self.stdout.write(f"Descargando {max_id} movimientos de Generación {gen} desde PokeAPI ({workers} hilos)...")
            moves_list = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(self.fetch_move_data, m_id): m_id for m_id in range(1, max_id + 1)}
                done = 0
                for f in concurrent.futures.as_completed(futures):
                    res = f.result()
                    if res:
                        moves_list.append(res)
                    done += 1
                    if done % 50 == 0 or done == max_id:
                        self.stdout.write(f"Descargados: {done}/{max_id} movimientos...")

            moves_list.sort(key=lambda x: x["id"])

            os.makedirs(os.path.dirname(MOVES_FILE_PATH), exist_ok=True)
            with open(MOVES_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(moves_list, f, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.SUCCESS(f"Copia de seguridad guardada en: {MOVES_FILE_PATH}"))

        self.stdout.write("Guardando movimientos en la base de datos...")
        with transaction.atomic():
            for m in moves_list:
                Move.objects.update_or_create(
                    name=m["name"],
                    defaults={
                        "id": m["id"],
                        "display_name": m["display_name"],
                        "generation": m["generation"],
                        "type": m["type"],
                        "power": m["power"],
                        "accuracy": m["accuracy"],
                        "pp": m["pp"],
                        "damage_class": m["damage_class"],
                        "effect_description": m["effect_description"],
                        "raw_data": m["raw_data"],
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"¡Finalizado! Se registraron {len(moves_list)} movimientos en la base de datos."))
