# Empeche la mise en veille du PC tant que ce script tourne (longue serie de tests, bots).
# Aucun reglage de Windows n'est change : la demande vient de ce processus et disparait avec lui.
#   powershell -ExecutionPolicy Bypass -File dev\_tools\keep-awake.ps1               (2 heures)
#   powershell -ExecutionPolicy Bypass -File dev\_tools\keep-awake.ps1 -Minutes 480  (une nuit)
# S'arrete seul apres -Minutes, ou des que le fichier -StopFile existe.
param([int]$Minutes = 120, [string]$StopFile = (Join-Path $env:TEMP 'elin-keep-awake.stop'))

Add-Type @"
using System; using System.Runtime.InteropServices;
public static class Awake { [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f); }
"@

Remove-Item -LiteralPath $StopFile -ErrorAction SilentlyContinue
$end = (Get-Date).AddMinutes($Minutes)
while ((Get-Date) -lt $end -and -not (Test-Path -LiteralPath $StopFile)) {
    # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    [void][Awake]::SetThreadExecutionState([uint32]"0x80000003")
    Start-Sleep -Seconds 20
}
[void][Awake]::SetThreadExecutionState([uint32]"0x80000000")
"veille de nouveau permise"
