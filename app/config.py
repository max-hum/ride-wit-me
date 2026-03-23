from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "routes"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")

DEFAULT_PROFILE_PATH = DATA_DIR / "rider_profile.json"
DEFAULT_PRESETS_PATH = DATA_DIR / "presets.json"