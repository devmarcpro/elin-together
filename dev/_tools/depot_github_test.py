"""Le depot GitHub, sans le jeu et sans GitHub : le code du mod (ElinTogether/Helper/GitHubDepot.cs, compile seul
dans _tools/github_depot_cli) parle au faux GitHub local (_tools/fake_github.py). Chaque joueur est un processus,
comme un jeu. ~1 minute, aucune fenetre Elin, aucun appel vers le vrai GitHub.

    python _tools/depot_github_test.py

G0  refus clairs avant tout : cle absente, cle refusee, depot introuvable, depot public
G1  depot vide : personne n'heberge, rien a prendre ; un joueur y met un monde (verrou d'abord, monde ensuite)
G2  un monde existe et personne n'heberge : un autre joueur y met le sien, l'ancien reste dans l'historique
G3  celui qui heberge sauvegarde cinq fois : le monde est le dernier, l'historique garde tout
G4  deux joueurs prennent en meme temps un verrou libre, puis un verrou perime : un seul gagne, a chaque fois
G5  pendant qu'un joueur heberge, un autre ne peut ni prendre ni remplacer ; verrou perime (3 min a l'heure de
    GitHub) : il est repris, et l'ancien hebergeur l'apprend a son retour
G6  le monde a change pendant qu'un joueur etait coupe : son envoi est refuse, rien n'est ecrase
G7  pannes (500, limite de debit, coupure) : une erreur de reseau, pas "cle refusee" ; ensuite tout reprend
G8  taille : 19 Mo passe et revient identique, 21 Mo est refuse sans rien envoyer
G10 GitHub accepte une sauvegarde mais sa reponse se perd : renvoyee, elle est reconnue, pas prise pour le monde
    d'un autre
G11 un joueur coupe plus de 3 minutes, un autre heberge, sauvegarde et quitte : le battement en retard du premier
    ne reprend pas le verrou
G12 une sauvegarde gardee d'une session precedente ne remplace jamais un monde dont elle ne descend pas
G13 noms de depot refuses, depot renomme (301), monde trop gros au telechargement
G14 le verrou dit ou rejoindre celui qui tient le monde (champ "join" ajoute) : ecrit a la prise, relu par les
    autres, mis a jour au battement, efface quand il rend le monde ; un ancien verrou sans ce champ est lu sans erreur
G9  la cle n'est nulle part ailleurs que dans l'en-tete Authorization ; aucune ecriture forcee
"""
import base64
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CLI = TOOLS / "github_depot_cli"
PORT = 55560
API = f"http://127.0.0.1:{PORT}"
TOKEN = "ghp_TESTJETON_ne_pas_voir"
REPO = "test/monde"
RESULTS = []
SAID = []  # tout ce que les joueurs ont ecrit (reponses et erreurs completes) : la cle n'y est jamais
TMP = Path(tempfile.mkdtemp(prefix="depot_github_"))


def check(label, good):
    RESULTS.append((label, bool(good)))
    print(f"    [{'OK' if good else 'ECHEC'}] {label}")
    if not good:
        for line in SAID[-4:]:  # ce que les joueurs viennent de recevoir
            print("        " + line[:300])


def ctl(where, **asked):
    request = urllib.request.Request(API + where, json.dumps(asked).encode() if where != "/__state" else None)
    with urllib.request.urlopen(request, timeout=30) as reply:
        return json.loads(reply.read())


def repo():
    return ctl("/__state")["repos"][REPO]


def requests():
    return len(ctl("/__state")["log"])


def lock():
    held = repo()["files"].get("lock.json")
    return json.loads(held["text"]) if held else {}


def holder():
    return lock().get("name", "")


def world(mark, size=0):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        z.writestr(zipfile.ZipInfo("game.txt"), mark)  # (sans date : la meme marque donne les memes octets)
        if size:
            z.writestr("big.bin", os.urandom(size))  # (ne se compresse pas : le zip fait cette taille)
    return data.getvalue()


def blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


class Player:
    """Un jeu : un processus qui garde en memoire ce qu'il a pris, comme le mod."""

    def __init__(self, name, token=TOKEN, depot=REPO, join=None):
        self.name = name
        self.file = TMP / f"{name}.zip"
        env = dict(os.environ, DEPOT_TOKEN=token, ELINTOGETHER_GITHUB_API=API)
        self.process = subprocess.Popen(
            ["dotnet", str(CLI / "bin" / "Release" / "net6.0" / "github_depot_cli.dll"), depot, f"PC-{name}:1", name]
            + ([join] if join else []),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", env=env)

    def ask(self, line):
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()
        answer = self.process.stdout.readline().rstrip("\n")
        SAID.append(f"{self.name} {line} -> {answer}")
        return answer

    def put(self, data, descends=""):
        """descends : l'empreinte du monde du depot dont cette sauvegarde vient (sauvegarde d'une session precedente)"""
        self.file.write_bytes(data if isinstance(data, bytes) else world(data))
        return self.ask(f"PUT {self.file} {descends}".rstrip())

    def take(self):
        """(reponse, marque du monde recu)"""
        answer = self.ask(f"TAKE {self.file}")
        return answer, zipfile.ZipFile(self.file).read("game.txt").decode() if answer.startswith("OK") else None

    def close(self):
        self.process.stdin.close()
        self.process.wait(10)


def together(*asks):
    """Les demandes partent en meme temps ; le faux GitHub retient les ecritures du verrou jusqu'a les avoir toutes."""
    ctl("/__fault", barrier=len(asks), path="lock.json")
    answers = [None] * len(asks)

    def run(i):
        answers[i] = asks[i]()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(len(asks))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ctl("/__fault")
    return answers


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    built = subprocess.run(["dotnet", "build", str(CLI), "-c", "Release", "-nologo", "-v", "q"],
                           capture_output=True, text=True)
    if built.returncode:
        print(built.stdout[-3000:])
        sys.exit("github_depot_cli ne compile pas")

    fake = subprocess.Popen([sys.executable, str(TOOLS / "fake_github.py"), "--port", str(PORT), "--token", TOKEN])
    players = []

    def player(*args, **more):
        players.append(Player(*args, **more))
        return players[-1]

    try:
        time.sleep(1)
        ctl("/__repo", name=REPO, private=True)
        ctl("/__repo", name="test/public", private=False)
        a, b, c, d = (player(n) for n in "ABCD")

        print("--- G0")
        before = requests()
        check("cle absente : refuse sans rien demander a GitHub",
              player("X", token="").ask("WHO") == "NO password" and requests() == before)
        check("cle refusee (401) : refuse, et une seule demande est partie",
              player("X", token="ghp_fausse").put("monde de X") == "NO password" and requests() == before + 1)
        check("depot introuvable", player("X", depot="test/rien").ask("WHO") == "NO missing")
        answer = player("X", depot="test/public").put("monde public")
        check(f"depot public : refuse ({answer}), rien n'y est ecrit",
              answer == "NO public" and not ctl("/__state")["repos"]["test/public"]["files"])

        print("--- G1")
        check("depot vide : personne n'heberge", a.ask("WHO") == "OK ")
        check("rien a prendre, et le verrou n'est pas garde", a.take()[0] == "NO empty" and holder() == "")
        sent = world("monde de A")
        check("un joueur y met un monde", a.put(sent) == "OK ")
        files = repo()["files"]
        check("le depot a le monde (meme empreinte git) et dit qui heberge",
              files["world.zip"]["sha"] == blob_sha(sent) and holder() == "A")
        writes = [e["path"].rsplit("/", 1)[1] for e in ctl("/__state")["log"] if e["method"] == "PUT" and e["status"] in (200, 201)]
        check(f"le verrou est ecrit avant le monde ({writes[-2:]})", writes[-2:] == ["lock.json", "world.zip"])
        check("il quitte : le depot est libre", a.ask("RELEASE") == "OK " and holder() == "" and b.ask("WHO") == "OK ")

        print("--- G2")
        check("personne n'heberge : un autre joueur y met le sien", b.put("nouvelle partie de B") == "OK ")
        history = [h["sha"] for h in repo()["history"] if h["path"] == "world.zip"]
        check("le monde est le nouveau, l'ancien reste dans l'historique",
              repo()["files"]["world.zip"]["sha"] == history[-1] and blob_sha(sent) in history[:-1])

        print("--- G3")
        check("B prend le monde qu'il vient de mettre", b.take() == ("OK ", "nouvelle partie de B"))
        answers = [b.put(f"sauvegarde {i} de B") for i in range(5)]
        last = world("sauvegarde 4 de B")
        check("cinq sauvegardes : toutes recues, le monde est la derniere",
              answers == ["OK "] * 5 and repo()["files"]["world.zip"]["size"] == len(last))
        check("l'historique garde les sept mondes",
              len([h for h in repo()["history"] if h["path"] == "world.zip"]) == 7)
        check("battement : B heberge toujours", b.ask("BEAT") == "OK " and holder() == "B")

        print("--- G5")
        check("pendant que B heberge, C voit qui heberge", c.ask("WHO") == "OK B")
        check("C ne peut pas prendre le monde", c.take()[0] == "NO held B")
        before = repo()["files"]["world.zip"]["sha"]
        check("ni le remplacer, et on lui dit qui heberge", c.put("monde de C") == "NO held B")
        check("le monde n'a pas change", repo()["files"]["world.zip"]["sha"] == before)
        ctl("/__clock", offset=120)
        check("2 minutes sans battement (heure de GitHub) : B heberge encore", c.ask("WHO") == "OK B")
        ctl("/__clock", offset=250)
        check("plus de 3 minutes : le verrou est perime, le depot est libre", c.ask("WHO") == "OK ")
        check("C reprend le verrou perime et recoit la derniere sauvegarde de B",
              c.take() == ("OK ", "sauvegarde 4 de B") and holder() == "C")
        check("B revient : son battement apprend que C heberge", b.ask("BEAT") == "NO held C")
        check("sa sauvegarde est refusee", b.put("sauvegarde tardive de B") == "NO held C")
        check("le monde n'a pas change", repo()["files"]["world.zip"]["sha"] == before)

        print("--- G6")
        check("C sauvegarde puis quitte", c.put("sauvegarde de C") == "OK " and c.ask("RELEASE") == "OK ")
        there = repo()["files"]["world.zip"]["sha"]
        # B n'a pas quitte : son jeu a toujours en memoire le monde qu'il avait pris, que C a remplace depuis
        answer = b.put("sauvegarde de B apres la coupure")
        check(f"le monde a change entre-temps : l'envoi de B est refuse ({answer})", answer == "NO changed")
        check("rien n'est ecrase, et B ne garde pas le verrou",
              repo()["files"]["world.zip"]["sha"] == there and holder() == "")
        before = requests()
        check("ses battements et sauvegardes suivants ne touchent plus au depot",
              b.ask("BEAT") == "NO changed" and b.put("encore B") == "NO changed" and requests() == before)
        check("D prend le monde : c'est celui de C", d.take() == ("OK ", "sauvegarde de C"))
        ctl("/__write", repo=REPO, path="world.zip", content=base64.b64encode(world("ecrit a la main")).decode())
        check("quelqu'un ecrit world.zip a la main pendant que D heberge : l'envoi de D est refuse",
              d.put("sauvegarde de D") == "NO changed"
              and repo()["files"]["world.zip"]["sha"] == blob_sha(world("ecrit a la main")))
        check("B retourne a l'ecran titre puis reprend : il recoit le monde du depot",
              b.ask("RELEASE") == "OK " and b.take() == ("OK ", "ecrit a la main"))
        check("et ses sauvegardes passent de nouveau", b.put("B rejoue") == "OK " and b.ask("RELEASE") == "OK ")
        d.ask("RELEASE")

        print("--- G4")
        wins = []
        for i in range(10):
            got = together(c.take, d.take)
            won = [p for p, (answer, _) in zip((c, d), got) if answer == "OK "]
            lost = [answer for answer, _ in got if answer != "OK "]
            wins.append(len(won) == 1 and lost == [f"NO held {won[0].name}"] and holder() == won[0].name)
            if not wins[-1]:
                print("       ", got)
            for p in won:
                p.ask("RELEASE")
        refused = len([e for e in ctl("/__state")["log"] if e["status"] == 409 and e["path"].endswith("lock.json")])
        check(f"verrou libre, deux preneurs en meme temps, 10 fois : un seul gagne, l'autre apprend qui ({sum(wins)}/10)",
              all(wins))
        check(f"et c'est bien GitHub qui a departage (409 sur le verrou : {refused})", refused >= 10)
        wins = []
        offset = 250
        for i in range(5):
            check_holder = a.take()[0] == "OK "  # A heberge, puis disparait sans relacher
            offset += 250
            ctl("/__clock", offset=offset)
            got = together(c.take, d.take)
            won = [p for p, (answer, _) in zip((c, d), got) if answer == "OK "]
            wins.append(check_holder and len(won) == 1 and holder() == won[0].name
                        and [answer for answer, _ in got if answer != "OK "] == [f"NO held {won[0].name}"])
            if not wins[-1]:
                print("       ", got)
            for p in won:
                p.ask("RELEASE")
            a.ask("RELEASE")
        check(f"verrou perime, deux repreneurs en meme temps, 5 fois : un seul gagne ({sum(wins)}/5)", all(wins))

        print("--- G7")
        check("C heberge", c.take()[0] == "OK ")
        there = repo()["files"]["world.zip"]["sha"]
        ctl("/__fault", status=500, count=1)
        answer = c.put("pendant la panne")
        check(f"GitHub repond 500 : erreur de reseau ({answer[:60]}...)", answer.startswith("ERR System.IO.IOException"))
        ctl("/__fault", status=403, retry_after=60, count=1)
        answer = c.ask("BEAT")
        check("limite de debit (403 + Retry-After) : erreur de reseau, pas 'cle refusee'",
              answer.startswith("ERR System.IO.IOException"))
        ctl("/__fault", status=403, count=1)
        check("403 sans limite de debit (cle sans le droit d'ecrire) : cle refusee", c.ask("BEAT") == "NO password")
        ctl("/__fault", drop=20)
        answer = c.ask("BEAT")
        ctl("/__fault")
        check(f"connexion coupee : erreur de reseau ({answer[:70]}...)", answer.startswith("ERR System.IO.IOException"))
        check("pendant les pannes, le monde du depot n'a pas bouge", repo()["files"]["world.zip"]["sha"] == there)
        check("apres la panne, la sauvegarde passe", c.put("apres la panne") == "OK "
              and repo()["files"]["world.zip"]["sha"] == blob_sha(world("apres la panne")))

        print("--- G8")
        big = world("gros monde", 19 * 1024 * 1024)
        t = time.time()
        check(f"un monde de {len(big) / 1048576:.1f} Mo est accepte", c.put(big) == "OK ")
        check(f"et revient identique ({time.time() - t:.1f} s l'envoi)",
              c.ask("RELEASE") == "OK " and d.take()[0] == "OK " and d.file.read_bytes() == big)
        before = requests()
        check("21 Mo : refuse avec la raison, sans rien envoyer",
              d.put(world("trop gros", 21 * 1024 * 1024)) == "NO too big" and requests() == before)
        d.ask("RELEASE")

        print("--- G10")
        there = lambda: repo()["files"]["world.zip"]["sha"]  # noqa: E731
        worlds = lambda: len([h for h in repo()["history"] if h["path"] == "world.zip"])  # noqa: E731
        check("A prend le monde", a.take()[0] == "OK ")
        before = worlds()
        ctl("/__fault", lose="world.zip")
        first = a.put("sauvegarde dont la reponse se perd")
        again = a.put("sauvegarde dont la reponse se perd")
        check(f"GitHub accepte la sauvegarde, sa reponse se perd ({first[:36]}...) : renvoyee, elle est reconnue ({again})",
              again == "OK " and worlds() == before + 1)
        ctl("/__fault", lose="world.zip")
        first = a.put("encore une reponse perdue")
        answer = a.put("la sauvegarde suivante")
        check(f"puis une autre sauvegarde : le monde du depot est reconnu comme le sien, elle passe ({answer})",
              answer == "OK " and there() == blob_sha(world("la sauvegarde suivante")))
        ctl("/__fault")

        print("--- G11")
        offset += 250
        ctl("/__clock", offset=offset)  # A est coupe plus de 3 minutes
        check("pendant la coupure de A, B prend le monde, sauvegarde et quitte",
              b.take()[0] == "OK " and b.put("B pendant la coupure de A") == "OK " and b.ask("RELEASE") == "OK ")
        answer = a.ask("BEAT")
        check(f"le battement en retard de A ne reprend pas le verrou ({answer})", answer == "NO changed" and holder() == "")
        check("et le monde de B est toujours la", there() == blob_sha(world("B pendant la coupure de A")))
        a.ask("RELEASE")

        print("--- G12")
        old, now_there = blob_sha(world("la sauvegarde suivante")), there()
        e = player("E")  # un jeu relance : il n'a rien en memoire, seulement ce que dit son marqueur
        answer = e.put("vieille sauvegarde de E", descends=old)
        check(f"sauvegarde gardee, qui descend d'un monde que le depot n'a plus : refusee ({answer})", answer == "NO changed")
        check("rien n'est ecrase et le verrou est rendu", there() == now_there and holder() == "")
        answer = player("F").put("suite de F", descends=now_there)
        check(f"sauvegarde gardee qui descend du monde du depot : acceptee ({answer})",
              answer == "OK " and there() == blob_sha(world("suite de F")))
        players[-1].ask("RELEASE")
        check("le refus ne laisse rien derriere lui : E met ensuite une autre partie dans le depot",
              e.put("autre partie de E") == "OK " and e.ask("RELEASE") == "OK ")

        print("--- G13")
        before = requests()
        answers = [player("X", depot=bad).ask("WHO") for bad in ("../monde", "test/..", "t\u00e9st/monde", "test/mon de")]
        check(f"noms de depot refuses sans rien demander ({answers})",
              answers == ["NO missing"] * 4 and requests() == before)
        ctl("/__fault", status=301, count=1)
        check("depot renomme (301) : 'depot introuvable, verifiez le nom'", c.ask("WHO") == "NO missing")
        small = there()
        ctl("/__write", repo=REPO, path="world.zip",
            content=base64.b64encode(world("trop gros dans le depot", 21 * 1024 * 1024)).decode())
        answer = c.take()[0]
        check(f"monde de 21 Mo dans le depot : pas telecharge en entier, refuse ({answer}), verrou rendu",
              answer == "NO too big" and holder() == "")
        ctl("/__write", repo=REPO, path="world.zip", content=base64.b64encode(world("autre partie de E")).decode())
        check("(le depot retrouve son monde)", there() == small)

        print("--- G14")
        join = "76561198000000001 0"
        j = player("J", join=join)
        check("J prend le monde : le verrou garde ses trois champs et dit ou le rejoindre",
              j.take()[0] == "OK " and lock().get("join") == join and {"id", "name", "beat"} <= set(lock()))
        check("un autre joueur lit qui tient le monde, et ou le rejoindre",
              c.ask("WHO") == "OK J" and c.ask("JOIN") == "OK " + join)
        check("refuse a la prise, il le sait aussi, et n'a rien ecrit",
              c.take()[0] == "NO held J" and c.ask("JOIN") == "OK " + join and lock().get("id") == "PC-J:1")
        opened = "76561198000000001 109775241000000001"
        j2 = player("J", join=opened)  # (le meme jeu, une fois sa partie ouverte : son salon est connu)
        check("au battement suivant le verrou porte le salon",
              j2.ask("BEAT") == "OK " and lock().get("join") == opened and c.ask("WHO") == "OK J"
              and c.ask("JOIN") == "OK " + opened)
        check("J rend le monde : le champ est efface",
              j.ask("RELEASE") == "OK " and "join" not in lock() and c.ask("WHO") == "OK " and c.ask("JOIN") == "OK ")
        beat = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + offset))
        old = json.dumps({"id": "PC-OLD:1", "name": "Ancien", "beat": beat}, separators=(",", ":"))
        ctl("/__write", repo=REPO, path="lock.json", content=base64.b64encode(old.encode()).decode())
        answers = [c.ask("WHO"), c.ask("JOIN"), c.take()[0]]
        check(f"ancien verrou sans ce champ : lu sans erreur, tenu, rien pour rejoindre ({answers})",
              answers == ["OK Ancien", "OK ", "NO held Ancien"])
        offset += 250
        ctl("/__clock", offset=offset)
        check("perime, il se reprend comme avant ; un joueur qui ne dit pas ou le rejoindre ecrit un verrou sans ce champ", c.ask("WHO") == "OK " and c.take()[0] == "OK "
              and "join" not in lock() and c.ask("RELEASE") == "OK ")

        print("--- G9")
        log = ctl("/__state")["log"]
        check(f"{len(log)} demandes : la cle n'est que dans l'en-tete Authorization",
              not any(e["token_in_url"] or e["token_in_body"] or e["token_in_other_header"] for e in log))
        check("aucune ecriture ne force ni ne choisit une branche (seulement message, content, sha)",
              all(set(e["body_keys"]) <= {"message", "content", "sha"} for e in log))
        check(f"la cle n'est dans rien de ce que les joueurs ont ecrit ({len(SAID)} lignes, erreurs completes comprises)",
              any(line.split(" -> ")[1].startswith("ERR") for line in SAID) and not any(TOKEN in line for line in SAID))
        check("ni dans les fichiers recus", not any(TOKEN.encode() in p.read_bytes() for p in TMP.iterdir()))
        check("ni dans le depot (fichiers et messages de l'historique)", TOKEN not in json.dumps(repo()))
    finally:
        for p in players:
            try:
                p.close()
            except Exception:
                p.process.kill()
        fake.kill()
        fake.wait()
        shutil.rmtree(TMP, ignore_errors=True)

    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
