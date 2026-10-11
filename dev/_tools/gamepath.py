"""Ou est le jeu : variable d'environnement ELIN_GAME_PATH, sinon l'emplacement habituel de Steam."""
import os
from pathlib import Path

_USUAL = (r"G:\SteamLibrary\steamapps\common\Elin", r"C:\Program Files (x86)\Steam\steamapps\common\Elin")
GAME = Path(os.environ.get("ELIN_GAME_PATH") or next((p for p in _USUAL if os.path.exists(p)), _USUAL[-1]))
