# Lance Elin en serveur : une fenetre que personne ne joue, qui charge une sauvegarde et ouvre la partie toute
# seule. Les joueurs la rejoignent par adresse (onglet Lobby, "Join by address") : <adresse de ce PC>:55556.
# La sauvegarde doit avoir une base (un terrain revendique). Fermer la fenetre arrete le serveur.
$ErrorActionPreference = 'Stop'

# la meme recherche du jeu que l'installateur
$source = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'install.ps1') -Raw
Invoke-Expression ([regex]::Match($source, '(?s)function Find-Elin \{.*?\r?\n\}').Value)
$elin = Find-Elin
if (-not $elin) { Write-Host 'Elin introuvable.' -ForegroundColor Red; exit 1 }

$data = Join-Path $env:USERPROFILE 'AppData\LocalLow\Lafrontier\Elin'
$saves = @()
foreach ($root in @(@('Save', ''), @('Cloud Save', 'cloud:'))) {
    $dir = Join-Path $data $root[0]
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    foreach ($d in Get-ChildItem -LiteralPath $dir -Directory) {
        $file = @('game.txt', 'cloud.zip') | ForEach-Object { Join-Path $d.FullName $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if ($file) { $saves += [pscustomobject]@{ Id = $root[1] + $d.Name; Date = (Get-Item -LiteralPath $file).LastWriteTime } }
    }
}
$saves = @($saves | Sort-Object Date -Descending)
if ($saves.Count -eq 0) { Write-Host 'Aucune sauvegarde trouvee.' -ForegroundColor Red; exit 1 }

Write-Host 'Quelle sauvegarde le serveur doit-il heberger ?'
for ($i = 0; $i -lt $saves.Count; $i++) { Write-Host ("  {0}. {1}   ({2:dd/MM/yyyy HH:mm})" -f ($i + 1), $saves[$i].Id, $saves[$i].Date) }
$n = 0
if (-not [int]::TryParse((Read-Host 'Numero'), [ref]$n) -or $n -lt 1 -or $n -gt $saves.Count) { Write-Host 'Numero inconnu.' -ForegroundColor Red; exit 1 }
$save = $saves[$n - 1].Id

Start-Process -FilePath (Join-Path $elin 'Elin.exe') -WorkingDirectory $elin -ArgumentList @('-screen-fullscreen', '0', '-screen-width', '1280', '-screen-height', '720', '-empserver', $save)
Write-Host ''
Write-Host "Serveur lance sur la sauvegarde $save. Il met une a deux minutes a ouvrir la partie." -ForegroundColor Green
Write-Host 'Pour rejoindre : ecran titre, bouton Elin Together, onglet Lobby, "Join by address".'
Write-Host '  - depuis ce PC          : 127.0.0.1:55556'
Write-Host '  - depuis le meme reseau : l''adresse de ce PC sur le reseau, puis :55556'
foreach ($ip in (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' })) {
    Write-Host ("      {0}:55556" -f $ip.IPAddress)
}
Write-Host '  - depuis Internet       : ouvrir le port 55556 (UDP) de la box vers ce PC, ou utiliser un reseau prive'
Write-Host '                            (Tailscale, ZeroTier...) et donner l''adresse que ce reseau attribue a ce PC.'
