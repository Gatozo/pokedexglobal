import json
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from typing import Dict, Any


DEFAULT_FIXTURE_PATH = settings.BASE_DIR / 'tracker' / 'fixtures' / 'pokedex_entries.json'


def get_fixture_info(file_path: Path = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    """
    Retorna informacion sobre el estado actual del archivo de fixture.
    """
    try:
        rel_path = file_path.relative_to(settings.BASE_DIR).as_posix()
    except ValueError:
        rel_path = file_path.name

    if not file_path.exists():
        return {
            'exists': False,
            'file_name': file_path.name,
            'relative_path': rel_path,
            'size_human': '0 KB',
            'last_modified': None,
            'records_count': 0,
        }

    stat = file_path.stat()
    size_bytes = stat.st_size
    if size_bytes >= 1024 * 1024:
        size_human = f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        size_human = f"{size_bytes / 1024:.1f} KB"

    last_modified = datetime.fromtimestamp(stat.st_mtime)

    records_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                records_count = len(data)
    except Exception:
        pass

    return {
        'exists': True,
        'file_name': file_path.name,
        'relative_path': rel_path,
        'size_human': size_human,
        'last_modified': last_modified,
        'records_count': records_count,
    }


def export_tracker_fixtures(file_path: Path = DEFAULT_FIXTURE_PATH) -> Dict[str, Any]:
    """
    Exporta los modelos estructurales y personalizados de la Pokedex
    (Game, Pokedex, PokedexEntry) a un archivo fixture JSON en codificacion UTF-8.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        call_command(
            'dumpdata',
            'tracker.Game',
            'tracker.Pokedex',
            indent=2,
            stdout=f
        )

    return get_fixture_info(file_path)
