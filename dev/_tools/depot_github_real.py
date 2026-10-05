"""Le depot GitHub contre le VRAI GitHub, sans le jeu : le meme C# que le mod (github_depot_cli), deux joueurs.

    python _tools/depot_github_real.py devmarcpro/elin-together-monde-essai

La cle est celle que git a deja sur ce PC (git credential), gardee en memoire et passee au seul processus du test :
elle n'est ecrite nulle part. A n'utiliser que sur un depot prive d'essai : le test y ecrit lock.json et world.zip.

Ce que ce test ne prouve pas : le jeu lui-meme (SaveDepot, fil d'arriere-plan, HttpWebRequest de Mono).
"""
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

CLI = Path(__file__).parent / "github_depot_cli"
RESULTS = []


def check(label, good):
    RESULTS.append((label, good))
    print(f"    [{'OK' if good else 'ECHEC'}] {label}", flush=True)
    return good


class Player:
    def __init__(self, depot, name, token):
        env = dict(os.environ, DEPOT_TOKEN=token)
        env.pop("ELINTOGETHER_GITHUB_API", None)
        self.name = name
        self.process = subprocess.Popen(
            ["dotnet", str(CLI / "bin" / "Release" / "net6.0" / "github_depot_cli.dll"), depot, f"PC-{name}:1", name],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", env=env)

    def ask(self, line):
        t = time.time()
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()
        reply = self.process.stdout.readline().strip()
        print(f"  {self.name} {line.split(' ')[0]:8s} -> {reply[:110]}   ({time.time() - t:.1f} s)", flush=True)
        return reply

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=30)


def main():
    depot = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8")
    cred = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n", capture_output=True, text=True).stdout
    token = [line.split("=", 1)[1] for line in cred.splitlines() if line.startswith("password=")][0]
    built = subprocess.run(["dotnet", "build", str(CLI), "-c", "Release", "-nologo", "-v", "q"], capture_output=True, text=True)
    if built.returncode != 0:
        print(built.stdout[-2000:])
        sys.exit(1)

    tmp = Path(tempfile.mkdtemp(prefix="depot-real-"))
    stamp = str(time.time()).encode()
    w1, w2, w3 = tmp / "w1.zip", tmp / "w2.zip", tmp / "w3.zip"
    w1.write_bytes(b"PK" + stamp + os.urandom(1_600_000))   # une vraie partie : ~1,5 Mo ; au-dela de 1 Mo le JSON ne rend plus le contenu
    w2.write_bytes(b"PK" + stamp + os.urandom(2_100_000))
    w3.write_bytes(b"PK" + stamp + os.urandom(300_000))
    a, b = Player(depot, "A", token), Player(depot, "B", token)
    try:
        who = a.ask("WHO")
        if "held" in who.lower() and not who.startswith("OK"):
            print("le depot est tenu : attendre 3 minutes ou relacher a la main")
        got = a.ask(f"TAKE {tmp / 'a0.zip'}")
        empty = got == "NO empty"
        check(f"A prend le monde, ou apprend que le depot est vide ({got[:60]})", got.startswith("OK") or empty)
        if not empty:
            check(f"B, pendant ce temps, est refuse et apprend qui heberge ({(r := b.ask(f'TAKE {tmp / chr(98)}0.zip'))[:60]})", r == "NO held A")
        check(f"A envoie un monde de 1,6 Mo ({(r := a.ask(f'PUT {w1}'))[:40]})", r.startswith("OK"))
        check(f"A bat ({(r := a.ask('BEAT'))[:40]})", r.startswith("OK"))
        check(f"A relache ({(r := a.ask('RELEASE'))[:40]})", r.startswith("OK"))
        got = b.ask(f"TAKE {tmp / 'b1.zip'}")
        check(f"B prend le monde ({got[:60]})", got.startswith("OK"))
        check("B a recu exactement les octets envoyes par A (lecture au-dela de 1 Mo)",
              (tmp / "b1.zip").exists() and (tmp / "b1.zip").read_bytes() == w1.read_bytes())
        check(f"B envoie un monde de 2,1 Mo ({(r := b.ask(f'PUT {w2}'))[:40]})", r.startswith("OK"))
        check(f"A, qui n'a plus le monde, ne peut pas envoyer le sien ({(r := a.ask(f'PUT {w3}'))[:60]})", r.startswith("NO"))
        check(f"B relache ({(r := b.ask('RELEASE'))[:40]})", r.startswith("OK"))

        # les deux en meme temps : GitHub departage
        replies = {}
        threads = [threading.Thread(target=lambda p=p: replies.__setitem__(p.name, p.ask(f"TAKE {tmp / (p.name + '2.zip')}"))) for p in (a, b)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        winners = [n for n, r in replies.items() if r.startswith("OK")]
        check(f"deux preneurs en meme temps : un seul gagne ({winners})", len(winners) == 1)
        if winners:
            won = a if winners[0] == "A" else b
            check("le gagnant a recu le monde de B (2,1 Mo)", (tmp / (won.name + "2.zip")).read_bytes() == w2.read_bytes())
            check(f"le gagnant relache ({(r := won.ask('RELEASE'))[:40]})", r.startswith("OK"))
    finally:
        for p in (a, b):
            try:
                p.ask("RELEASE")
                p.close()
            except Exception:  # noqa: BLE001
                pass
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
