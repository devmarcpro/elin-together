# Retire la version "independance" d'ElinTogether et reactive la version Workshop si elle est installee.
$ErrorActionPreference = 'Stop'
$ModId = 'dk.elinplugins.elintogether'

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
Write-Host '=== Desinstallation d''ElinTogether (version independance) ===' -ForegroundColor Cyan
Write-Host ''

if (Get-Process -Name Elin -ErrorAction SilentlyContinue) {
    Write-Host 'Elin est ouvert : ferme le jeu puis relance.' -ForegroundColor Red
    exit 1
}

$elin = Find-Elin
if (-not $elin) {
    $elin = (Read-Host 'Colle ici le chemin du dossier d''Elin (celui qui contient Elin.exe)').Trim('"', ' ')
    if (-not (Test-Path -LiteralPath (Join-Path $elin 'Elin.exe'))) {
        Write-Host 'Elin.exe introuvable. Annule.' -ForegroundColor Red
        exit 1
    }
}
$elin = Get-RealPath $elin
Write-Host "Elin trouve : $elin"

$dest = Join-Path $elin 'Package\Mod_ElinTogether'
$backupRoot = Join-Path $elin '_ElinTogether_sauvegarde'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
if (Test-Path -LiteralPath $dest) {
    Move-Item -LiteralPath $dest -Destination (Join-Path $backupRoot "Mod_ElinTogether-retire-$stamp")
    Write-Host 'Mod retire de Elin\Package (garde dans le dossier de sauvegarde).'
} else {
    Write-Host 'Le mod n''etait pas installe dans Elin\Package.'
}

$loadorder = Join-Path $elin 'loadorder.txt'
if (Test-Path -LiteralPath $loadorder) {
    Copy-Item -LiteralPath $loadorder -Destination (Join-Path $backupRoot "loadorder-avant-retrait-$stamp.txt")
    $lines = @(Get-Content -LiteralPath $loadorder -Encoding UTF8)
    $suffix = ",0,$ModId"
    $out = foreach ($line in $lines) {
        if ($line -match ",[01],$([regex]::Escape($ModId))$") {
            $path = $line.Substring(0, $line.Length - $suffix.Length)
            if ($path.TrimEnd('\') -ieq $dest.TrimEnd('\')) { continue }
            "$path,1,$ModId"
        } else { $line }
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($loadorder, [string[]]@($out), $utf8)
    Write-Host 'Liste des mods remise comme avant (version Workshop reactivee si elle est installee).'
}

Write-Host ''
Write-Host 'Desinstallation terminee.' -ForegroundColor Green
