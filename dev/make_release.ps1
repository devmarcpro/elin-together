# Fabrique la version a distribuer : build Release du fork, dossier avec l'installateur, zip.
# Usage : .\make_release.ps1            -> _release\ElinTogether-independance.zip
# Le build Release remplace le build de dev dans Elin\Package\Mod_ElinTogether (relancer .\build.ps1 pour tester).
param([string]$Name = "ElinTogether-independance")

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
. (Join-Path $root "game-path.ps1")
$game = $ElinGame
$mod = Join-Path $game "Package\Mod_ElinTogether"

& (Join-Path $root "build.ps1") Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "Le build Release a echoue."
    exit 1
}

$out = Join-Path $root "_release\$Name"
if (Test-Path -LiteralPath $out) { Remove-Item -LiteralPath $out -Recurse -Force }
New-Item -ItemType Directory -Force -Path $out | Out-Null

Copy-Item -Path (Join-Path $root "_release\template\*") -Destination $out
Copy-Item -LiteralPath $mod -Destination (Join-Path $out "Mod_ElinTogether") -Recurse
# fichier fabrique par le jeu a partir du classeur, qui garde les anciens textes : le jeu le refait au lancement
Remove-Item -LiteralPath (Join-Path $out "Mod_ElinTogether\LangMod\EN\SourceLocalization.json") -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath (Join-Path $out "Mod_ElinTogether") -Filter *.pdb -Recurse | Remove-Item -Force

$version = (Get-Content -LiteralPath (Join-Path $game "version.json") -Raw | ConvertFrom-Json).versionText
Set-Content -LiteralPath (Join-Path $out "version-elin.txt") -Value $version -Encoding ascii

$zip = Join-Path $root "_release\$Name.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -Path $out -DestinationPath $zip

# le meme mod pour Mac (CrossOver, Whisky, Wine), avec son installateur
python (Join-Path $root "_tools\make_mac_zip.py") $zip

$commit = git -C (Join-Path $root "..") rev-parse --short HEAD
"Version prete : $zip"
"Elin $version, commit $commit, $((Get-Item -LiteralPath $zip).Length / 1MB -as [int]) Mo"
