# Renomme la fenetre principale d'un processus (pour distinguer l'hote du joueur pendant un test a la main).
# Usage : title.ps1 <pid> <titre>
param([int]$ProcessId, [string]$Title)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WinTitle {
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern bool SetWindowText(IntPtr hWnd, string text);
}
"@

$process = Get-Process -Id $ProcessId -ErrorAction Stop
if ($process.MainWindowHandle -eq 0) { "pas de fenetre pour $ProcessId"; exit 1 }
[WinTitle]::SetWindowText($process.MainWindowHandle, $Title) | Out-Null
"$ProcessId -> $Title"
