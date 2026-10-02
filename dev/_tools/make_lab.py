"""Cree _lab/Elin2 : un lanceur pour une 2e instance d'Elin sur le meme PC.

Elin a forceSingleInstance = True (PlayerSettings) : une 2e instance se ferme avant meme de demarrer Unity.
Ce dossier contient des liens vers le vrai jeu (jonctions + liens physiques, pas de copie de 2 Go)
et une copie de globalgamemanagers ou seul le drapeau forceSingleInstance passe a 0.
Le dossier du jeu n'est pas modifie (hors steam_appid.txt, ajoute a la main).

    PYTHONPATH=_tools/pylib python _tools/make_lab.py [Elin2] [2]   # (re)cree le lanceur _lab/<nom>, identite de test
    _lab/Elin2/Elin.exe -screen-fullscreen 0 -screen-width 1280 -screen-height 720 -logFile <chemin>

A relancer apres chaque mise a jour d'Elin (les liens physiques pointent vers les anciens fichiers).
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import sys

import UnityPy

sys.path.insert(0, str(Path(__file__).parent))
from gamepath import GAME  # noqa: E402

LAB = Path(__file__).resolve().parent.parent / "_lab" / "Elin2"
IDENTITY = 2

JUNCTION_DIRS = ["Custom", "MonoBleedingEdge", "Package", "User"]
# BepInEx : dossier reel ; config/ est copie (la 1re instance garde les .cfg ouverts -> sharing violation)
BEPINEX_JUNCTIONS = ["core", "patchers", "plugins"]
BEPINEX_COPIES = ["config"]
LINK_FILES = ["Elin.exe", "UnityPlayer.dll", "UnityCrashHandler64.exe", "doorstop_config.ini", "winhttp.dll",
              "version.json", "steam_appid.txt"]


def junction(link: Path, target: Path):
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)


def remove_lab():
    if not LAB.exists():
        return
    # jonctions d'abord (os.rmdir retire le lien sans toucher la cible)
    children = list(LAB.iterdir())
    for sub in ("Elin_Data", "BepInEx"):
        if (LAB / sub).exists() and not (LAB / sub).is_junction():
            children += list((LAB / sub).iterdir())
    for p in children:
        if p.is_junction():
            os.rmdir(p)
    shutil.rmtree(LAB)


def patched_globalgamemanagers() -> bytes:
    """Octets de globalgamemanagers avec forceSingleInstance = 0, en ne changeant qu'un seul octet."""
    src = GAME / "Elin_Data" / "globalgamemanagers"
    raw = bytearray(src.read_bytes())
    env = UnityPy.load(str(src))
    obj = next(o for o in env.objects if o.type.name == "PlayerSettings")

    tree = obj.read_typetree()
    assert tree["forceSingleInstance"] is True, "drapeau deja a False ?"
    before = obj.get_raw_data()
    tree["forceSingleInstance"] = False
    after = obj.save_typetree(tree)

    assert len(before) == len(after), "la taille de l'objet a change"
    diffs = [i for i in range(len(before)) if before[i] != after[i]]
    assert len(diffs) == 1, f"attendu 1 octet modifie, obtenu {len(diffs)}"

    start = obj.byte_start
    assert raw[start:start + len(before)] == before, "objet introuvable a byte_start"
    raw[start + diffs[0]] = after[diffs[0]]
    print(f"forceSingleInstance : octet {start + diffs[0]:#x} {before[diffs[0]]} -> {after[diffs[0]]}")
    return bytes(raw)


def main():
    remove_lab()
    LAB.mkdir(parents=True)

    for d in JUNCTION_DIRS:
        junction(LAB / d, GAME / d)
    for f in LINK_FILES:
        os.link(GAME / f, LAB / f)

    bep = LAB / "BepInEx"
    bep.mkdir()
    for d in BEPINEX_JUNCTIONS:
        junction(bep / d, GAME / "BepInEx" / d)
    for d in BEPINEX_COPIES:
        shutil.copytree(GAME / "BepInEx" / d, bep / d)

    data = LAB / "Elin_Data"
    data.mkdir()
    for p in (GAME / "Elin_Data").iterdir():
        if p.name == "globalgamemanagers":
            continue
        if p.is_dir():
            junction(data / p.name, p)
        else:
            os.link(p, data / p.name)
    (data / "globalgamemanagers").write_bytes(patched_globalgamemanagers())

    # identite de test : plusieurs instances sur un meme compte Steam = joueurs distincts (build DEBUG)
    cfg = bep / "config" / "dk.elinplugins.elintogether.cfg"
    text = cfg.read_text(encoding="utf-8")
    if re.search(r"^Identity = \d+", text, re.MULTILINE):
        text = re.sub(r"^Identity = \d+", f"Identity = {IDENTITY}", text, flags=re.MULTILINE)
    else:
        text = re.sub(r"^\[Dev\]\r?\n", f"[Dev]\n\nIdentity = {IDENTITY}\n", text, count=1, flags=re.MULTILINE)
    cfg.write_text(text, encoding="utf-8")

    # loadorder : memes mods, mais les chemins Package pointent vers la jonction du lanceur
    lines = (GAME / "loadorder.txt").read_text(encoding="utf-8").splitlines()
    lines = [l.replace(str(GAME / "Package"), str(LAB / "Package")) for l in lines]
    (LAB / "loadorder.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    check = UnityPy.load(str(data / "globalgamemanagers"))
    ps = next(o for o in check.objects if o.type.name == "PlayerSettings").read_typetree()
    print("verification : forceSingleInstance =", ps["forceSingleInstance"], "| productName =", ps["productName"])
    print("lanceur pret :", LAB / "Elin.exe")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        LAB = LAB.parent / sys.argv[1]
    if len(sys.argv) > 2:
        IDENTITY = int(sys.argv[2])
    main()
