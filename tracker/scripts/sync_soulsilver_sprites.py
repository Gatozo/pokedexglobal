"""
Script para sincronizar localmente los sprites estáticos oficiales de Pokémon Plata SoulSilver
desde los assets ya sincronizados de Pokémon Oro HeartGold, garantizando paridad total.
"""
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
HG_DIR = MEDIA_DIR / "heartgold"
HG_SHINY_DIR = MEDIA_DIR / "heartgold_shiny"
SS_DIR = MEDIA_DIR / "soulsilver"
SS_SHINY_DIR = MEDIA_DIR / "soulsilver_shiny"

def main():
    print("Sincronizando sprites estáticos de Oro HeartGold a Plata SoulSilver...")
    
    if not HG_DIR.exists():
        print(f"Error: {HG_DIR} no existe. Primero sincroniza HeartGold.")
        return

    # Sincronización idempotente
    if not SS_DIR.exists():
        shutil.copytree(HG_DIR, SS_DIR)
        print(f"Directorio {SS_DIR} creado y poblado.")
    else:
        print(f"Directorio {SS_DIR} ya existe, omitiendo copia de seguridad.")

    if not SS_SHINY_DIR.exists():
        shutil.copytree(HG_SHINY_DIR, SS_SHINY_DIR)
        print(f"Directorio {SS_SHINY_DIR} creado y poblado.")
    else:
        print(f"Directorio {SS_SHINY_DIR} ya existe, omitiendo copia de seguridad.")

    print("Sincronización de sprites estáticos finalizada con éxito.")

if __name__ == "__main__":
    main()
