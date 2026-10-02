"""Fabrique le paquet a emporter sur une autre machine : tout le dossier de travail en un zip, sans rien qui
depende de cette machine.

    python dev/_tools/make_transfer.py [destination.zip]      # defaut : <dossier parent>/ElinMods-transfert.zip

Sont laisses de cote : les raccourcis (jonctions) et les copies du jeu faites de liens vers le jeu (`_lab/Elin*`,
`*/lab`), qui recopieraient le jeu plusieurs fois et ne marcheraient pas ailleurs ; les produits de compilation
(`obj`, `.vs`). Le script `dev/apres-deplacement.ps1` remet les raccourcis et refait les copies a l'arrivee.
"""
import os
import stat
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
ROOT = REPO.parent
SKIP_NAMES = {"obj", ".vs", "__pycache__"}


def is_link(path):
    try:
        st = os.lstat(path)
    except OSError:
        return True
    return bool(getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT) or stat.S_ISLNK(st.st_mode)


def skip_dir(path: Path):
    if is_link(path) or path.name in SKIP_NAMES:
        return True
    # copies du jeu : des liens vers l'installation de cette machine
    if path.name == "lab" and (path / "Host").exists():
        return True
    if path.parent.name == "_lab" and path.name.startswith("Elin"):
        return True
    return False


def main():
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / f"{ROOT.name}-transfert.zip"
    count = size = 0
    skipped = []
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for folder, dirs, files in os.walk(ROOT):
            folder = Path(folder)
            keep = []
            for d in dirs:
                if skip_dir(folder / d):
                    skipped.append(str((folder / d).relative_to(ROOT)))
                else:
                    keep.append(d)
            dirs[:] = keep
            if not dirs and not files:
                zf.writestr(str(folder.relative_to(ROOT.parent)).replace("\\", "/") + "/", "")
            for f in files:
                p = folder / f
                if is_link(p):
                    continue
                try:
                    zf.write(p, str(p.relative_to(ROOT.parent)).replace("\\", "/"))
                    count += 1
                    size += p.stat().st_size
                except OSError as ex:
                    skipped.append(f"{p.relative_to(ROOT)} ({ex.strerror})")
    print(f"{dest} : {count} fichiers, {size / 1e6:.0f} Mo avant compression, {dest.stat().st_size / 1e6:.0f} Mo")
    print("laisses de cote :")
    for s in sorted(skipped):
        print("  " + s)


if __name__ == "__main__":
    main()
