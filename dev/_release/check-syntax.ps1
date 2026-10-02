# Verifie la syntaxe des scripts de l'installateur.
foreach ($name in 'install.ps1', 'uninstall.ps1') {
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot "template\$name"), [ref]$null, [ref]$errors) | Out-Null
    "$name : $($errors.Count) erreur(s)"
    $errors | ForEach-Object { "  ligne $($_.Extent.StartLineNumber) : $($_.Message)" }
}
