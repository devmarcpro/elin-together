"""Client du pont de debug d'ElinTogether (EmpDebugListener, builds DEBUG uniquement).

Chaque instance d'Elin ecoute sur le premier port libre de 127.0.0.1:27551-27560.

    python emp.py ports                      # instances qui repondent (pid, role, port)
    python emp.py [-p PORT] hello
    python emp.py [-p PORT] state
    python emp.py [-p PORT] cmd "emp.add_local"
    python emp.py [-p PORT] eval "EClass.pc.Name"
    python emp.py [-p PORT] shot [0.5]      # capture via Unity, affiche le chemin du PNG
"""
import argparse
import json
import socket
import sys

PORTS = range(27551, 27561)


def call(port, op, args=None, timeout=90.0):
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
        s.sendall((json.dumps({"id": 1, "op": op, "args": args or {}}) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.decode("utf-8"))


def live_ports():
    found = []
    for port in PORTS:
        try:
            r = call(port, "hello", timeout=2.0)
        except OSError:
            continue
        if r.get("ok"):
            found.append(r["result"])
    return found


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--port", type=int, help="port de l'instance (defaut : la premiere qui repond)")
    ap.add_argument("op", choices=["ports", "hello", "state", "cmd", "eval", "shot"])
    ap.add_argument("arg", nargs="?")
    a = ap.parse_args()

    if a.op == "ports":
        print(json.dumps(live_ports(), indent=2, ensure_ascii=False))
        return

    port = a.port
    if port is None:
        live = live_ports()
        if not live:
            sys.exit("aucune instance d'Elin avec le pont de debug (build DEBUG lance ?)")
        port = live[0]["port"]

    if a.op == "cmd":
        r = call(port, "command", {"cmd": a.arg})
    elif a.op == "eval":
        r = call(port, "eval", {"code": a.arg}, timeout=120.0)
    elif a.op == "shot":
        r = call(port, "screenshot", {"scale": float(a.arg or 0.5)})
    else:
        r = call(port, a.op)

    print(json.dumps(r, indent=2, ensure_ascii=False))
    if not r.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
