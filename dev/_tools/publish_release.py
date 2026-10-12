"""Publie une preversion du fork sur GitHub avec l'identifiant que git a deja. usage : publish.py <version> <commit entier> <note.md> <zip>"""
import hashlib
import io
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

version, commit, note, zip_path = sys.argv[1:5]

# La barriere : _tools/release_gate.sh doit avoir tourne, tout vert, sur CE code (le mod et ses textes ; les notes et
# les outils peuvent avoir change depuis). Sans elle : --sans-barriere "la raison", ecrite dans la note du journal.
tree = lambda path: subprocess.run(['git', 'rev-parse', commit + ':' + path], capture_output=True, text=True).stdout.strip()  # noqa: E731
code = tree('ElinTogether') + '-' + tree('package')
gate_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_shots', 'gate.txt')
gate = io.open(gate_path, encoding='utf-8', errors='replace').read() if os.path.exists(gate_path) else ''
if '--sans-barriere' in sys.argv:
    print('PUBLIE SANS BARRIERE :', sys.argv[sys.argv.index('--sans-barriere') + 1])
elif ('code ' + code) not in gate or 'BARRIERE OK' not in gate:
    print("Refuse : la barriere de version n'est pas verte pour ce code.")
    print('  bash _tools/release_gate.sh   (PC libre, une heure et demie), puis relancer ; ou --sans-barriere "raison"')
    print('  etat :', (gate.strip().splitlines() or ['pas de fichier _shots/gate.txt'])[-1])
    raise SystemExit(2)
cred = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', capture_output=True, text=True).stdout
token = [line.split('=', 1)[1] for line in cred.splitlines() if line.startswith('password=')][0]
HEADERS = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'elin-together-release'}


def call(url, data=None, headers=None):
    h = dict(HEADERS)
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h)) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, e.read().decode()[:500])
        raise SystemExit(1)


body = io.open(note, encoding='utf-8').read()
rel = call('https://api.github.com/repos/devmarcpro/elin-together/releases', json.dumps({
    'tag_name': 'independance-' + version, 'target_commitish': commit,
    # version-elin.txt : écrit par make_release.ps1 dans le dossier à côté du zip
    'name': f"Indépendance {version} (Elin {open(zip_path[:-4] + '/version-elin.txt').read().strip()})",
    'body': body, 'prerelease': True, 'draft': False}).encode(), {'Content-Type': 'application/json'})
print('release', rel['html_url'], 'prerelease', rel['prerelease'])
data = open(zip_path, 'rb').read()
asset = call(rel['upload_url'].split('{')[0] + '?name=ElinTogether-independance.zip', data, {'Content-Type': 'application/zip'})
print('asset', asset['size'], asset['browser_download_url'])
public = urllib.request.urlopen(urllib.request.Request(asset['browser_download_url'], headers={'User-Agent': 'x'})).read()
print('local ', len(data), hashlib.sha256(data).hexdigest())
print('public', len(public), hashlib.sha256(public).hexdigest(), 'IDENTIQUE' if public == data else 'DIFFERENT')
mac = zip_path[:-4] + '-mac.zip'
if os.path.exists(mac):
    asset = call(rel['upload_url'].split('{')[0] + '?name=ElinTogether-independance-mac.zip', open(mac, 'rb').read(), {'Content-Type': 'application/zip'})
    print('mac  ', asset['size'], asset['browser_download_url'])
