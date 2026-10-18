"""Rutas del prototipo, relativas a este archivo (no dependen del directorio de ejecución)."""
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
WEEK10_DIR = CODE_DIR.parent
DELIVERIES_DIR = WEEK10_DIR.parent

# Se busca primero en week10/data y, si no está, en los datos procesados de la Semana 7.
DATA_DIRS = [WEEK10_DIR / "data", DELIVERIES_DIR / "week07" / "data"]
MODELS_DIR = WEEK10_DIR / "models"


def find_data_file(name: str) -> Path:
    for d in DATA_DIRS:
        p = d / name
        if p.exists():
            return p
    searched = ", ".join(str(d) for d in DATA_DIRS)
    raise FileNotFoundError(f"No se encontró '{name}'. Carpetas revisadas: {searched}")
