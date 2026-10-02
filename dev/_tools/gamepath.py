"""Ou est le jeu : variable d'environnement ELIN_GAME_PATH, sinon l'emplacement habituel de Steam."""
import os
from pathlib import Path

GAME = Path(os.environ.get("ELIN_GAME_PATH") or r"C:\Program Files (x86)\Steam\steamapps\common\Elin")
