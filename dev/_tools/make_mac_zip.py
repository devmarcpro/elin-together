"""Le zip pour Mac, a partir du zip a distribuer : memes fichiers du mod, l'installateur Mac et sa notice, chemins
avec des / (le zip de Windows a des \\, qu'un Mac ne lit pas comme des dossiers) et le droit d'execution.
usage : make_mac_zip.py <ElinTogether-independance.zip>   ->  ElinTogether-independance-mac.zip a cote"""
import sys
import zipfile
from pathlib import Path

src_path = Path(sys.argv[1])
out = src_path.with_name(src_path.stem + "-mac.zip")
template = Path(__file__).parent.parent / "_release" / "template"
root = src_path.stem + "-mac/"


def add(z, name, data, when, mode=0o644):
    info = zipfile.ZipInfo(root + name, date_time=when)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = mode << 16
    z.writestr(info, data)


with zipfile.ZipFile(src_path) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for item in src.infolist():
        name = item.filename.replace(chr(92), "/").split("/", 1)[-1]
        if (name.startswith("Mod_ElinTogether/") and not name.endswith("/")) or name == "version-elin.txt":
            add(z, name, src.read(item), item.date_time)
    when = max(i.date_time for i in src.infolist())
    for name, mode in (("Installer-Mac.command", 0o755), ("LISEZMOI-MAC.txt", 0o644)):
        add(z, name, (template / name).read_bytes().replace(b"\r\n", b"\n"), when, mode)

print(f"Version Mac prete : {out}")
