"""Faux GitHub local : seulement ce dont le depot GitHub du mod se sert (GitHubDepot.cs), sans dependance.

    python _tools/fake_github.py --port 55560 --token <jeton attendu>

Ce qu'il imite (API "Contents") :
    GET  /repos/{o}/{r}                     -> {"private": ...} ; 404 si le depot n'existe pas
    GET  /repos/{o}/{r}/contents/           -> liste [{name, path, sha, size, type}] ; 404 si le depot est vide
    GET  /repos/{o}/{r}/contents/{chemin}   -> JSON {sha, content (base64)} ; les octets si Accept contient "raw"
    PUT  /repos/{o}/{r}/contents/{chemin}   -> corps {message, content, sha?} ; fichier existant sans sha : 422 ;
                                               sha qui n'est plus le bon : 409 ; sinon 200/201 avec content.sha
    Le sha est celui de git : sha1("blob <taille>\\0" + octets). Chaque ecriture reste dans l'historique.
    Sans "Authorization: Bearer <jeton>" : 401. Sans User-Agent : 403 (comme le vrai).

Ce qui se pilote (sans jeton), pour les tests :
    POST /__repo   {"name": "o/r", "private": true}        cree ou vide un depot
    POST /__clock  {"offset": 240}                          l'en-tete Date = l'heure vraie + tant de secondes
    POST /__fault  {"status": 500, "count": 2}              les 2 prochaines demandes recoivent 500
                   {"status": 403, "retry_after": 60, "count": 1}   limite de debit
                   {"drop": 1}                              la prochaine demande est coupee sans reponse
                   {"slow": 3}                              chaque demande attend 3 s
                   {"barrier": 2, "path": "lock.json"}      les PUT de ce fichier attendent d'etre 2, puis partent
                                                            ensemble (la course de deux joueurs)
                   {"lose": "world.zip"}                    le prochain PUT de ce fichier est accepte, mais sa
                                                            reponse se perd (connexion coupee)
                   {}                                       plus de panne
    POST /__write  {"repo": "o/r", "path": "world.zip", "content": "<base64>"}   quelqu'un ecrit un fichier a la main
    GET  /__state  -> depots (fichiers, historique) et journal des demandes
"""
import argparse
import base64
import hashlib
import json
import threading
import time
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
REPOS = {}  # "o/r" -> {"private": bool, "files": {chemin: octets}, "history": [{path, sha, message, date}]}
LOG = []  # une ligne par demande faite a l'API
FAULT = {}
STATE = {"token": "", "offset": 0.0, "barrier": None, "lose": None}


def blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def now():
    return time.time() + STATE["offset"]


def store(repo, path, data, message):
    repo["files"][path] = data
    repo["history"].append({"path": path, "sha": blob_sha(data), "message": message,
                            "date": formatdate(now(), usegmt=True)})


class Handler(BaseHTTPRequestHandler):
    server_version = "FakeGitHub"
    protocol_version = "HTTP/1.1"  # (comme le vrai : la connexion reste ouverte si le client le veut)

    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except ConnectionError:
            pass  # (un jeu qui se ferme coupe la connexion qu'il gardait ouverte)

    def date_time_string(self, timestamp=None):
        return formatdate(now(), usegmt=True)

    def reply(self, status, body, headers=None, raw=False):
        data = body if raw else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/octet-stream" if raw else "application/json")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)
        return status

    def do_GET(self):
        self.route("GET")

    def do_PUT(self):
        self.route("PUT")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path.startswith("/__"):
            return self.control(json.loads(body or b"{}"))

        token = STATE["token"]
        auth = self.headers.get("Authorization", "")
        entry = {"method": method, "path": self.path, "auth": auth == "Bearer " + token,
                 "token_in_url": token in self.path, "token_in_body": token.encode() in body,
                 "token_in_other_header": any(token in v for k, v in self.headers.items() if k != "Authorization"),
                 "accept": self.headers.get("Accept", ""), "body_keys": [], "status": 0}
        with LOCK:
            LOG.append(entry)
            fault = dict(FAULT)
            for limited in ("count", "drop"):
                if FAULT.get(limited):
                    FAULT[limited] -= 1
                    if not FAULT[limited]:
                        FAULT.clear()

        if fault.get("slow"):
            time.sleep(fault["slow"])
        if fault.get("drop"):
            entry["status"] = -1
            self.close_connection = True
            return
        if fault.get("status"):
            headers = {"Retry-After": str(fault["retry_after"])} if fault.get("retry_after") else {}
            entry["status"] = self.reply(fault["status"], {"message": "fault"}, headers)
            return

        entry["status"] = self.api(method, body, auth, entry)

    def api(self, method, body, auth, entry):
        if not self.headers.get("User-Agent"):
            return self.reply(403, {"message": "Request forbidden by administrative rules (no User-Agent)"})
        if auth != "Bearer " + STATE["token"]:
            return self.reply(401, {"message": "Bad credentials"})

        parts = self.path.split("?")[0].split("/", 5)  # "", repos, o, r, contents, chemin
        if len(parts) < 4 or parts[1] != "repos":
            return self.reply(404, {"message": "Not Found"})
        name = parts[2] + "/" + parts[3]
        path = parts[5] if len(parts) > 5 else ""
        barrier = STATE["barrier"]
        if method == "PUT" and barrier and path == barrier[1]:
            try:
                barrier[0].wait(5)
            except threading.BrokenBarrierError:
                pass

        with LOCK:
            repo = REPOS.get(name)
            if repo is None:
                return self.reply(404, {"message": "Not Found"})
            if len(parts) == 4:
                return self.reply(200, {"full_name": name, "private": repo["private"]})
            if parts[4] != "contents":
                return self.reply(404, {"message": "Not Found"})
            files = repo["files"]

            if method == "GET" and path == "":
                if not files:
                    return self.reply(404, {"message": "This repository is empty."})
                return self.reply(200, [{"name": p, "path": p, "sha": blob_sha(d), "size": len(d), "type": "file"}
                                        for p, d in files.items()])
            if method == "GET":
                if path not in files:
                    return self.reply(404, {"message": "Not Found"})
                data = files[path]
                if "raw" in self.headers.get("Accept", ""):
                    return self.reply(200, data, raw=True)
                # (comme le vrai : au-dela de 1 Mo, le JSON ne porte plus le contenu)
                content = base64.encodebytes(data).decode() if len(data) <= 1_000_000 else ""
                return self.reply(200, {"name": path, "path": path, "sha": blob_sha(data), "size": len(data),
                                        "content": content, "encoding": "base64"})
            if method == "PUT":
                asked = json.loads(body)
                entry["body_keys"] = sorted(asked)
                if path in files:
                    if "sha" not in asked:
                        return self.reply(422, {"message": "Invalid request. \"sha\" wasn't supplied."})
                    if asked["sha"] != blob_sha(files[path]):
                        return self.reply(409, {"message": path + " does not match " + asked["sha"]})
                elif "sha" in asked:
                    return self.reply(409, {"message": path + " does not match " + asked["sha"]})
                created = path not in files
                data = base64.b64decode(asked["content"])
                store(repo, path, data, asked.get("message", ""))
                if STATE["lose"] == path:
                    STATE["lose"] = None
                    self.close_connection = True
                    return -2
                return self.reply(201 if created else 200,
                                  {"content": {"name": path, "path": path, "sha": blob_sha(data), "size": len(data)}})
            return self.reply(404, {"message": "Not Found"})

    def control(self, asked):
        with LOCK:
            if self.path == "/__repo":
                REPOS[asked["name"]] = {"private": asked.get("private", True), "files": {}, "history": []}
            elif self.path == "/__clock":
                STATE["offset"] = float(asked["offset"])
            elif self.path == "/__fault":
                FAULT.clear()
                FAULT.update({k: v for k, v in asked.items() if k not in ("barrier", "path", "lose")})
                STATE["lose"] = asked.get("lose")
                STATE["barrier"] = (threading.Barrier(asked["barrier"]), asked["path"]) if asked.get("barrier") else None
            elif self.path == "/__write":
                store(REPOS[asked["repo"]], asked["path"], base64.b64decode(asked["content"]), "by hand")
            elif self.path == "/__state":
                return self.reply(200, {
                    "offset": STATE["offset"], "log": LOG,
                    "repos": {name: {"private": repo["private"], "history": repo["history"],
                                     "files": {p: {"sha": blob_sha(d), "size": len(d),
                                                   "text": d.decode("utf-8", "replace") if len(d) < 2000 else None}
                                               for p, d in repo["files"].items()}}
                              for name, repo in REPOS.items()}})
            else:
                return self.reply(404, {"message": "Not Found"})
            return self.reply(200, {})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=55560)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    STATE["token"] = args.token
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
