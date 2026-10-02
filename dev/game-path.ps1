# Ou est le jeu : ELIN_GAME_PATH, sinon l'emplacement habituel de Steam. Inclus par les autres scripts.
$ElinGame = if ($env:ELIN_GAME_PATH) { $env:ELIN_GAME_PATH } else { "C:\Program Files (x86)\Steam\steamapps\common\Elin" }
if (-not (Test-Path -LiteralPath (Join-Path $ElinGame "Elin.exe"))) {
    Write-Error "Elin introuvable dans '$ElinGame'. Regle la variable d'environnement ELIN_GAME_PATH sur le dossier du jeu."
    exit 1
}
# ...\steamapps\common\Elin -> ...\steamapps\workshop\content
$ElinWorkshop = Join-Path (Split-Path (Split-Path $ElinGame -Parent) -Parent) "workshop\content"
