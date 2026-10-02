# Compile le fork ElinTogether et le déploie dans Elin\Package\Mod_ElinTogether.
# Usage : .\build.ps1            (DebugNightly, active le pont de debug TCP)
#         .\build.ps1 Release    (ReleaseNightly)
# Le dossier du jeu : variable d'environnement ELIN_GAME_PATH, sinon l'emplacement habituel de Steam.
param([string]$Mode = "Debug")

. (Join-Path $PSScriptRoot "game-path.ps1")
$env:ElinGamePath = $ElinGame
$env:SteamContentPath = $ElinWorkshop

$config = if ($Mode -eq "Release") { "ReleaseNightly" } else { "DebugNightly" }

if (Get-Process -Name Elin -ErrorAction SilentlyContinue) {
    Write-Warning "Elin tourne : la DLL est verrouillee, ferme le jeu avant de compiler."
    exit 1
}

Push-Location (Join-Path $PSScriptRoot "..")
try {
    dotnet build ./ElinTogether -c $config
} finally {
    Pop-Location
}
