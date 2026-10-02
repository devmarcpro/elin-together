# A lancer une fois apres avoir copie le dossier de travail sur une autre machine (ou apres un simple clone).
# Remet les raccourcis entre dossiers, verifie ce qui manque, refabrique les copies du jeu pour les tests.
#   powershell -ExecutionPolicy Bypass -File dev\apres-deplacement.ps1          (tout)
#   powershell -ExecutionPolicy Bypass -File dev\apres-deplacement.ps1 -NoLab   (sans refaire les copies du jeu)
# Sans danger a relancer : il ne supprime que des raccourcis casses, jamais des fichiers.
param([switch]$NoLab)

$dev = $PSScriptRoot
$repo = Split-Path $dev -Parent
$root = Split-Path $repo -Parent
$todo = @()

function Is-Link($path) {
    $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    return $item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
}

function Remove-BrokenLink($path) {
    if ((Is-Link $path) -and -not (Test-Path -LiteralPath (Join-Path $path '.'))) {
        [System.IO.Directory]::Delete($path)
        "raccourci casse retire : $path"
    }
}

# 1. dossiers de travail hors depot : a cote du depot (ancienne disposition, dossier ElinMods) ou dans dev/
foreach ($name in '_lab', '_shots', '_decomp', '_backup') {
    $inDev = Join-Path $dev $name
    $beside = Join-Path $root $name
    Remove-BrokenLink $inDev
    if (Test-Path -LiteralPath $inDev) { continue }

    if ((Test-Path -LiteralPath $beside) -and -not (Is-Link $beside)) {
        New-Item -ItemType Junction -Path $inDev -Target $beside | Out-Null
        "raccourci cree : dev\$name -> $beside"
    } else {
        New-Item -ItemType Directory -Path $inDev | Out-Null
        "dossier cree : dev\$name"
    }
}

# 2. anciens chemins (ElinMods\_tools, ElinMods\_release) : seulement si on est dans l'ancienne disposition
$oldLayout = (Test-Path -LiteralPath (Join-Path $root '_lab')) -or (Test-Path -LiteralPath (Join-Path $root '_decomp'))
if ($oldLayout) {
    foreach ($name in '_tools', '_release') {
        $beside = Join-Path $root $name
        Remove-BrokenLink $beside
        if (-not (Test-Path -LiteralPath $beside) -and (Test-Path -LiteralPath (Join-Path $dev $name))) {
            New-Item -ItemType Junction -Path $beside -Target (Join-Path $dev $name) | Out-Null
            "raccourci cree : $beside -> dev\$name"
        }
    }
}

# 3. ce qui doit etre la
$pristine = Join-Path $dev '_lab\saves\world_lab.pristine'
if (Test-Path -LiteralPath $pristine) { "monde de test : present" }
else { $todo += "copier le monde de test (dossier world_lab.pristine de l'ancienne machine) dans $pristine" }

. (Join-Path $dev 'game-path.ps1')
if ($ElinGame -and (Test-Path -LiteralPath (Join-Path $ElinGame 'Elin.exe'))) {
    "jeu : $ElinGame"
    if (-not (Test-Path -LiteralPath (Join-Path $ElinGame 'steam_appid.txt'))) {
        $todo += "creer $ElinGame\steam_appid.txt contenant 2135150 (SETUP.md, etape 4.3)"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $ElinGame 'Package\Mod_ElinTogether\ElinTogether.dll'))) {
        $todo += "compiler le mod : powershell -ExecutionPolicy Bypass -File dev\build.ps1 (SETUP.md, etape 4.5)"
    }
    # les copies du jeu recopient ces deux fichiers, que le jeu et le mod creent a leur premier lancement
    if (-not (Test-Path -LiteralPath (Join-Path $ElinGame 'loadorder.txt')) -or
        -not (Test-Path -LiteralPath (Join-Path $ElinGame 'BepInEx\config\dk.elinplugins.elintogether.cfg'))) {
        $todo += "lancer Elin une fois avec le mod, le fermer (SETUP.md, etape 4.6), puis relancer ce script pour les copies du jeu"
        $NoLab = $true
    }
} else {
    $todo += "installer Elin par Steam, ou regler ELIN_GAME_PATH sur le dossier du jeu (SETUP.md, etape 4)"
    $NoLab = $true
}

$python = Get-Command python -ErrorAction SilentlyContinue
$pylib = Join-Path $dev '_tools\pylib\UnityPy'
if (-not $python) { $todo += "installer Python 3.12 (SETUP.md, etape 3)"; $NoLab = $true }
elseif (-not (Test-Path -LiteralPath $pylib)) {
    $todo += "installer les bibliotheques Python : python -m pip install --target dev/_tools/pylib -r dev/requirements.txt"
    $NoLab = $true
}
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { $todo += "installer le SDK .NET 11.0.100-preview.5.26302.115 (SETUP.md, etape 3)" }

# 4. copies du jeu pour les tests : ce sont des liens vers le jeu de CETTE machine, elles ne se transportent pas
if (-not $NoLab) {
    if (Get-Process -Name Elin -ErrorAction SilentlyContinue) {
        $todo += "fermer Elin puis relancer ce script pour refaire les copies du jeu"
    } else {
        $env:PYTHONPATH = Join-Path $dev '_tools\pylib'
        foreach ($copy in @(@('Elin2', '2'), @('Elin3', '3'), @('Elin4', '4'))) {
            python (Join-Path $dev '_tools\make_lab.py') $copy[0] $copy[1]
            if ($LASTEXITCODE -ne 0) { $todo += "la copie $($copy[0]) n'a pas pu etre faite : voir SETUP.md, etape 5" }
        }
        if (-not $env:ELINTOGETHER_LAB) {
            [Environment]::SetEnvironmentVariable('ELINTOGETHER_LAB', (Join-Path $dev '_lab'), 'User')
            "variable ELINTOGETHER_LAB reglee sur dev\_lab (pour le bouton du bot dans le menu du jeu)"
        }
    }
}

""
if ($todo.Count -eq 0) { "Tout est en place. Verification : voir SETUP.md, etape 7." }
else {
    "Reste a faire :"
    $todo | ForEach-Object { "  - $_" }
}
