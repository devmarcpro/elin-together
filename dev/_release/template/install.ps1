# Installe le mod ElinTogether (version "independance") dans Elin.
# Lance par Installer.bat. Ne modifie que : Elin\Package\Mod_ElinTogether et Elin\loadorder.txt (sauvegarde a cote).
$ErrorActionPreference = 'Stop'
$ModId = 'dk.elinplugins.elintogether'
$YkFramework = '3400020753'
$WorkshopElinTogether = '3773298709'
$AppId = '2135150'

function Find-Elin {
    $steamDirs = @()
    foreach ($key in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try {
            $p = Get-ItemProperty -Path $key -ErrorAction Stop
            foreach ($n in 'SteamPath', 'InstallPath') { if ($p.$n) { $steamDirs += ($p.$n -replace '/', '\') } }
        } catch {}
    }
    $steamDirs += 'C:\Program Files (x86)\Steam'
    $libs = @()
    foreach ($steam in ($steamDirs | Select-Object -Unique)) {
        $libs += $steam
        $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            foreach ($m in [regex]::Matches((Get-Content -LiteralPath $vdf -Raw), '"path"\s+"([^"]+)"')) {
                $libs += ($m.Groups[1].Value -replace '\\\\', '\')
            }
        }
    }
    foreach ($lib in ($libs | Select-Object -Unique)) {
        $elin = Join-Path $lib 'steamapps\common\Elin'
        if (Test-Path -LiteralPath (Join-Path $elin 'Elin.exe')) { return $elin }
    }
    return $null
}

# Chemin avec ses vraies majuscules (le registre de Steam le donne souvent en minuscules)
function Get-RealPath([string]$path) {
    $item = Get-Item -LiteralPath $path
    if ($null -eq $item.Parent) { return $item.FullName.ToUpper() }
    return Join-Path (Get-RealPath $item.Parent.FullName) ($item.Parent.GetDirectories($item.Name)[0].Name)
}

Write-Host ''
Write-Host '=== Installation d''ElinTogether (version independance) ===' -ForegroundColor Cyan
Write-Host ''

$source = Join-Path $PSScriptRoot 'Mod_ElinTogether'
if (-not (Test-Path -LiteralPath (Join-Path $source 'ElinTogether.dll'))) {
    Write-Host 'Le dossier Mod_ElinTogether est introuvable a cote de l''installateur.' -ForegroundColor Red
    Write-Host 'Dezippe tout le dossier avant de lancer Installer.bat.'
    exit 1
}

if (Get-Process -Name Elin -ErrorAction SilentlyContinue) {
    Write-Host 'Elin est ouvert : ferme le jeu puis relance l''installateur.' -ForegroundColor Red
    exit 1
}

$elin = Find-Elin
if (-not $elin) {
    Write-Host 'Elin n''a pas ete trouve automatiquement.' -ForegroundColor Yellow
    $elin = (Read-Host 'Colle ici le chemin du dossier d''Elin (celui qui contient Elin.exe)').Trim('"', ' ')
    if (-not (Test-Path -LiteralPath (Join-Path $elin 'Elin.exe'))) {
        Write-Host 'Elin.exe est introuvable dans ce dossier. Installation annulee.' -ForegroundColor Red
        exit 1
    }
}
$elin = Get-RealPath $elin
Write-Host "Elin trouve : $elin"

$version = ''
try { $version = (Get-Content -LiteralPath (Join-Path $elin 'version.json') -Raw | ConvertFrom-Json).versionText } catch {}
$expected = ''
$expectedFile = Join-Path $PSScriptRoot 'version-elin.txt'
if (Test-Path -LiteralPath $expectedFile) { $expected = (Get-Content -LiteralPath $expectedFile -Raw).Trim() }
if ($version) { Write-Host "Version d'Elin : $version" }
if ($expected -and $version -and $expected -ne $version) {
    Write-Host "Attention : ce mod a ete prepare pour Elin $expected." -ForegroundColor Yellow
    Write-Host 'Les deux joueurs doivent avoir la meme version du jeu : mets Elin a jour sur Steam.' -ForegroundColor Yellow
}

# dependance : YK Framework (Workshop)
$library = Split-Path (Split-Path (Split-Path $elin -Parent) -Parent) -Parent
$workshop = Join-Path $library "steamapps\workshop\content\$AppId"
if (-not (Test-Path -LiteralPath (Join-Path $workshop $YkFramework))) {
    Write-Host ''
    Write-Host 'Il manque le mod "YK Framework", dont ElinTogether a besoin.' -ForegroundColor Yellow
    Write-Host 'Abonne-toi sur le Workshop Steam, laisse Steam le telecharger, puis relance l''installateur :'
    Write-Host "  https://steamcommunity.com/sharedfiles/filedetails/?id=$YkFramework"
    Write-Host 'Le plus simple : abonne-toi a "Elin Together" sur le Workshop, il amene ce qu''il faut :'
    Write-Host "  https://steamcommunity.com/sharedfiles/filedetails/?id=$WorkshopElinTogether"
    exit 1
}

# copie du mod (l'ancienne copie locale est mise de cote, hors du dossier Package)
$dest = Join-Path $elin 'Package\Mod_ElinTogether'
$backupRoot = Join-Path $elin '_ElinTogether_sauvegarde'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (Test-Path -LiteralPath $dest) {
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
    Move-Item -LiteralPath $dest -Destination (Join-Path $backupRoot "Mod_ElinTogether-$stamp")
    Write-Host 'Ancienne version locale mise de cote.'
}
Copy-Item -LiteralPath $source -Destination $dest -Recurse
Write-Host 'Mod copie dans Elin\Package\Mod_ElinTogether.'

# liste des mods : la version locale active, la version Workshop (c'est le meme mod) desactivee
$loadorder = Join-Path $elin 'loadorder.txt'
$hasWorkshopCopy = Test-Path -LiteralPath (Join-Path $workshop $WorkshopElinTogether)
if (Test-Path -LiteralPath $loadorder) {
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
    Copy-Item -LiteralPath $loadorder -Destination (Join-Path $backupRoot "loadorder-$stamp.txt")
    $lines = @(Get-Content -LiteralPath $loadorder -Encoding UTF8)
    $found = $false
    $suffix = ",0,$ModId"
    $out = foreach ($line in $lines) {
        if ($line -match ",[01],$([regex]::Escape($ModId))$") {
            $path = $line.Substring(0, $line.Length - $suffix.Length)
            if ($path.TrimEnd('\') -ieq $dest.TrimEnd('\')) { $found = $true; "$dest,1,$ModId" } else { "$path,0,$ModId" }
        } else { $line }
    }
    if (-not $found) { $out = @($out) + "$dest,1,$ModId" }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($loadorder, [string[]]@($out), $utf8)
    Write-Host 'Liste des mods mise a jour (cette version activee, version Workshop desactivee).'
} elseif ($hasWorkshopCopy) {
    Write-Host ''
    Write-Host 'La liste des mods (loadorder.txt) n''existe pas encore.' -ForegroundColor Yellow
    Write-Host 'Lance Elin une fois, quitte le jeu, puis relance cet installateur pour desactiver la version Workshop.'
}

Write-Host ''
Write-Host 'Installation terminee.' -ForegroundColor Green
Write-Host 'Lance Elin par Steam. Sur l''ecran titre, le bouton Elin Together sert a heberger ou rejoindre une partie.'
Write-Host 'Les deux joueurs doivent avoir installe ce meme dossier.'
Write-Host "Sauvegardes : $backupRoot"
