# Bascule entre le build de dev et la version Workshop d'ElinTogether dans loadorder.txt.
# Usage : .\use-workshop.ps1        -> version Workshop active (pour jouer normalement)
#         .\use-workshop.ps1 -Dev   -> build de dev actif (pour tester le fork)
param([switch]$Dev)

. (Join-Path $PSScriptRoot "game-path.ps1")
$path = Join-Path $ElinGame "loadorder.txt"
$lines = Get-Content -LiteralPath $path -Encoding UTF8

$lines = $lines | ForEach-Object {
    if ($_ -match "\\Package\\Mod_ElinTogether,") {
        $_ -replace ",[01],dk\.elinplugins\.elintogether$", $(if ($Dev) { ",1,dk.elinplugins.elintogether" } else { ",0,dk.elinplugins.elintogether" })
    } elseif ($_ -match "\\3773298709,") {
        $_ -replace ",[01],dk\.elinplugins\.elintogether$", $(if ($Dev) { ",0,dk.elinplugins.elintogether" } else { ",1,dk.elinplugins.elintogether" })
    } else {
        $_
    }
}

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($path, [string[]]$lines, $utf8)
Get-Content -LiteralPath $path
