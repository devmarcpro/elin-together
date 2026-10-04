"""Elin Together Server, sans le jeu : on lui parle comme le fait le mod (SaveDepot.Ask) et on regarde son dossier.
Aucune fenetre Elin, ~10 secondes.

    python _tools/depot_proto_test.py

P1  serveur vide : un joueur y met un monde
P2  le serveur a deja un monde et personne ne l'heberge : un autre joueur y met le sien (une nouvelle partie),
    l'ancien monde est garde a part
P3  celui qui heberge sauvegarde cinq fois de suite : le monde remplace en P2 est toujours la
P4  pendant qu'il heberge, un autre ne peut ni prendre ni remplacer le monde, et on lui dit qui heberge
P5  mauvais mot de passe : refuse tout de suite, sans attendre les octets annonces (pas de memoire reservee
    pour quelqu'un qui n'a pas le mot de passe)
"""
import io
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

EXE = Path(__file__).resolve().parent.parent / "_release" / "template" / "ElinTogetherServer.exe"
PORT = 55559
RESULTS = []


def check(label, good):
    RESULTS.append((label, bool(good)))
    print(f"    [{'OK' if good else 'ECHEC'}] {label}")


def world(mark):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr("game.txt", mark)
    return data.getvalue()


def mark_of(path):
    with zipfile.ZipFile(path) as z:
        return z.read("game.txt").decode()


def ask(command, who, body=b"", password="", announce=None, timeout=10):
    """Une demande, comme SaveDepot.Ask. Renvoie (statut, octets)."""
    with socket.create_connection(("127.0.0.1", PORT), timeout=timeout) as s:
        length = len(body) if announce is None else announce
        s.sendall(f"{password}\n{command}\n{who}\n{who}\n{length}\n".encode() + body)
        f = s.makefile("rb")
        status = f.readline().decode().rstrip("\n")
        size = int(f.readline())
        return status, f.read(size)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(tempfile.mkdtemp(prefix="depot_proto_"))
    server = subprocess.Popen([str(EXE), "--depot", str(folder), "--port", str(PORT), "--password", "secret"])
    try:
        time.sleep(3)
        ok = lambda *a, **k: ask(*a, password="secret", **k)  # noqa: E731

        print("--- P1")
        check("serveur vide : personne n'heberge", ok("WHO", "A")[0] == "OK ")
        check("un joueur y met un monde", ok("PUT", "A", world("monde de A"))[0] == "OK")
        ok("RELEASE", "A")

        print("--- P2")
        status = ok("PUT", "B", world("nouvelle partie de B"))[0]
        check(f"un monde existe, personne n'heberge : un autre joueur y met le sien ({status})", status == "OK")
        check("le monde du serveur est le nouveau", mark_of(folder / "world.zip") == "nouvelle partie de B")
        kept = [p for p in folder.glob("replaced-*.zip") if mark_of(p) == "monde de A"]
        check("l'ancien monde est garde a part", len(kept) == 1)

        print("--- P3")
        ok("TAKE", "B")
        for i in range(5):
            ok("PUT", "B", world(f"sauvegarde {i} de B"))
        check("cinq sauvegardes plus tard, le monde du serveur est la derniere",
              mark_of(folder / "world.zip") == "sauvegarde 4 de B")
        check("et le monde remplace est toujours la",
              any(mark_of(p) == "monde de A" for p in folder.glob("*.zip")))

        print("--- P4")
        status = ok("TAKE", "C")[0]
        check(f"pendant que B heberge, C ne peut pas prendre le monde ({status})", status == "NO held B")
        status = ok("PUT", "C", world("monde de C"))[0]
        check(f"ni le remplacer, et on lui dit qui heberge ({status})", status == "NO held B")
        check("le monde n'a pas change", mark_of(folder / "world.zip") == "sauvegarde 4 de B")

        print("--- P5")
        t = time.time()
        try:
            status = ask("PUT", "X", b"", password="faux", announce=200_000_000, timeout=8)[0]
        except OSError as ex:
            status = type(ex).__name__
        check(f"mauvais mot de passe : refuse tout de suite ({status}, {time.time() - t:.1f} s)", status == "NO password")
    finally:
        server.kill()
        server.wait()
        shutil.rmtree(folder, ignore_errors=True)

    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
