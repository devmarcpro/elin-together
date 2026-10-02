"""Ajoute un client a un host deja lance (serveur local demarre) : ouvre _lab/Elin2 et le connecte.

    python _tools/launch_client.py
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import LAB_EXE, SHOTS, WINDOW, bridge_for, join_client, log, state, summary, wait  # noqa: E402

HOST = 27551


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    proc = subprocess.Popen([str(LAB_EXE), *WINDOW, "-logFile", str(SHOTS / "elin2-player.log")], cwd=LAB_EXE.parent)
    log(f"client lance (pid {proc.pid})")
    port = wait(lambda: bridge_for(proc.pid), "pont du client", timeout=600)
    wait(lambda: state(port).get("sceneMode") == "Title", "ecran titre du client", timeout=300)
    time.sleep(10)
    join_client(HOST, port, "client 1")
    print(summary("HOST  ", HOST))
    print(summary("CLIENT", port))


if __name__ == "__main__":
    main()
