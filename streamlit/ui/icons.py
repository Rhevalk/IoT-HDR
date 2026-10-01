from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def icon(name):
    path = BASE_DIR / "assets" / "icons" / f"{name}.svg"
    return path.read_text()
