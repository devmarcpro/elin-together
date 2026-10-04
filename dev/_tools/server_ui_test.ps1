# Joue les boutons d'Elin Together Server comme une main : clics postes aux vrais controles, boites lues.
#   powershell -ExecutionPolicy Bypass -File dev\_tools\server_ui_test.ps1 -Part depot   (sans Elin, dossier et port de test)
#   powershell -ExecutionPolicy Bypass -File dev\_tools\server_ui_test.ps1 -Part elin    (avec Elin : lance un Elin sans fenetre sur world_lab, 2 minutes)
# Pas joue : choisir un dossier dans Browse (la boite s'ouvre, on annule), le message 'The server could not start'.
param([string]$Part = "depot")
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class W {
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, string l);
}
"@
$exe = Join-Path $PSScriptRoot "..\_release\template\ElinTogetherServer.exe"
$depot = Join-Path $env:TEMP "ets-ui-depot"
$port = 55558
$AE = [System.Windows.Automation.AutomationElement]
$TS = [System.Windows.Automation.TreeScope]
$script:ok = 0; $script:ko = 0
function Check($what, $cond) { if ($cond) { $script:ok++; "    [OK] $what" } else { $script:ko++; "    [ECHEC] $what" } }
function Wins($procId) {
  $c = New-Object System.Windows.Automation.PropertyCondition($AE::ProcessIdProperty, $procId)
  @($AE::RootElement.FindAll($TS::Children, $c)) + @($AE::RootElement.FindAll($TS::Children, $c) | ForEach-Object { $_.FindAll($TS::Children, $c) } | ForEach-Object { $_ })
}
function Main($procId) { for ($n = 0; $n -lt 20; $n++) { $w = Wins $procId | Where-Object { $_.Current.ClassName -like "WindowsForms*" } | Select-Object -First 1; if ($w) { return $w }; Start-Sleep -Milliseconds 500 } }
function Box($procId) { for ($n = 0; $n -lt 20; $n++) { $b = Wins $procId | Where-Object { $_.Current.ClassName -eq "#32770" } | Select-Object -First 1; if ($b) { return $b }; Start-Sleep -Milliseconds 250 } }
function Kids($el) { $el.FindAll($TS::Descendants, [System.Windows.Automation.Condition]::TrueCondition) }
function Named($el, $name) { Kids $el | Where-Object { $_.Current.Name -like $name } | Select-Object -First 1 }
function Click($el) { [void][W]::PostMessage([IntPtr]$el.Current.NativeWindowHandle, 0xF5, [IntPtr]::Zero, [IntPtr]::Zero); Start-Sleep -Milliseconds 700 }
function Texts($el) { (Kids $el | Where-Object { $_.Current.Name } | ForEach-Object { $_.Current.Name -replace "\s+", " " }) -join " | " }
# repond a une boite : $answer = 6 (Yes), 7 (No), ou 0 (le seul bouton)
function Answer($procId, $answer) {
  $b = Box $procId
  if (-not $b) { return $null }
  $text = Texts $b
  $buttons = @(Kids $b | Where-Object { $_.Current.ClassName -eq "Button" })
  $want = @{ 6 = "^(Oui|Yes)$"; 7 = "^(Non|No)$" }
  $btn = if ($answer) { $buttons | Where-Object { $_.Current.Name -match $want[$answer] } | Select-Object -First 1 } else { $buttons[0] }
  Click $btn
  $text
}
function State($m) { (Kids $m | Where-Object { $_.Current.Name -match "^(Running|Stopped|Starting|Stopping)" } | Select-Object -First 1).Current.Name }
function Pick($m, $prefix) {
  $combo = Kids $m | Where-Object { $_.Current.ClassName -like "*COMBOBOX*" } | Select-Object -First 1
  [W]::SendMessage([IntPtr]$combo.Current.NativeWindowHandle, 0x14D, [IntPtr](-1), $prefix)
}
function Ask($command, $id, $name) {
  $c = New-Object System.Net.Sockets.TcpClient("127.0.0.1", $port); $s = $c.GetStream()
  $b = [Text.Encoding]::UTF8.GetBytes("`n$command`n$id`n$name`n0`n"); $s.Write($b, 0, $b.Length)
  $r = New-Object IO.StreamReader($s); $line = $r.ReadLine(); $c.Close(); $line
}

if ($Part -eq "depot") {
  Remove-Item $depot -Recurse -Force -ErrorAction SilentlyContinue
  $p = Start-Process $exe -ArgumentList "--depot `"$depot`" --port $port" -PassThru
  Start-Sleep 3
  $m = Main $p.Id
  "pid $($p.Id) : $(Texts $m)"
  Check "lance : Running, pas de monde" ((State $m) -eq "Running" -and (Texts $m) -match "No world yet")

  "--- B1 Put this save on the server (serveur vide)"
  $i = Pick $m "world_lab"
  Check "world_lab choisi dans la liste (rang $i)" ("$i" -ne "-1")
  Click (Named $m "Put this save*")
  $t = Answer $p.Id 0; "    boite : $t"
  Check "une boite dit que la sauvegarde est le monde du serveur" ($t -match "This save is now the world of the server")
  Check "world.zip existe" (Test-Path "$depot\world.zip")
  Start-Sleep 2; "    fenetre : $(Texts (Main $p.Id))"

  "--- B2 la remplacer : la boite demande, No ne change rien, Yes garde l'ancien"
  $stamp = (Get-Item "$depot\world.zip").LastWriteTime
  Click (Named $m "Put this save*")
  $t = Answer $p.Id 7; "    boite : $t"
  Check "boite de confirmation (replace)" ($t -match "already holds a world")
  Start-Sleep 1
  Check "No : rien ne change, pas d'autre boite" ((Get-Item "$depot\world.zip").LastWriteTime -eq $stamp -and -not (Get-ChildItem $depot -Filter "replaced-*") -and -not (Wins $p.Id | Where-Object { $_.Current.ClassName -eq "#32770" }))
  Click (Named $m "Put this save*")
  $t = Answer $p.Id 6
  $t2 = Answer $p.Id 0; "    boite : $t2"
  Check "Yes : monde remplace, l'ancien garde (replaced-*.zip)" ($t2 -match "now the world" -and @(Get-ChildItem $depot -Filter "replaced-*.zip").Count -eq 1)

  "--- B3 Stop / fermer pendant qu'un joueur heberge"
  "    TAKE : $(Ask 'TAKE' 'id1' 'Tester')"
  Start-Sleep 3
  $list = Kids (Main $p.Id) | Where-Object { $_.Current.ClassName -like "*LISTBOX*" } | Select-Object -First 1
  Check "la liste montre un joueur qui heberge" ([W]::SendMessage([IntPtr]$list.Current.NativeWindowHandle, 0x18B, [IntPtr]::Zero, $null).ToInt64() -eq 1)
  Click (Named $m "Stop")
  $t = Answer $p.Id 7; "    boite : $t"
  Check "Stop : la boite previent (Tester is hosting), No : toujours Running" ($t -match "Tester is hosting" -and (State (Main $p.Id)) -eq "Running")
  [void][W]::PostMessage([IntPtr]$m.Current.NativeWindowHandle, 0x10, [IntPtr]::Zero, [IntPtr]::Zero); Start-Sleep 1
  $t = Answer $p.Id 7
  Check "fermer la fenetre : meme boite, No : le logiciel reste ouvert" ($t -match "Tester is hosting" -and -not $p.HasExited)
  Click (Named $m "Stop")
  $t = Answer $p.Id 6; Start-Sleep 1
  Check "Stop, Yes : Stopped" ((State (Main $p.Id)) -eq "Stopped")

  "--- B4 port deja pris"
  $l = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Any, $port); $l.Start()
  Click (Named $m "Start")
  $t = Answer $p.Id 0; "    boite : $t"
  $l.Stop()
  Check "Start avec le port pris : une boite le dit, reste Stopped" ($t -match "already in use" -and (State (Main $p.Id)) -eq "Stopped")
  Click (Named $m "Start"); Start-Sleep 1
  Check "Start, port libre : Running, le monde est toujours la" ((State (Main $p.Id)) -eq "Running" -and (Texts (Main $p.Id)) -match "World: \d+ KB")

  "--- B5 Browse"
  Click (Named $m "Browse*")
  $b = Box $p.Id
  $t = if ($b) { Texts $b } else { "" }; "    boite : $t"
  Check "Browse ouvre le choix de dossier" ($t -match "Folder of an Elin save")
  if ($b) { Click (Kids $b | Where-Object { $_.Current.ClassName -eq "Button" -and $_.Current.Name -match "Annuler|Cancel" } | Select-Object -First 1) }

  Click (Named $m "Stop"); Start-Sleep 1
  [void][W]::PostMessage([IntPtr]$m.Current.NativeWindowHandle, 0x10, [IntPtr]::Zero, [IntPtr]::Zero); Start-Sleep 2
  Check "arrete puis ferme : le logiciel se ferme sans question" $p.HasExited
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
}

if ($Part -eq "elin") {
  $p = Start-Process $exe -PassThru
  Start-Sleep 3
  $m = Main $p.Id
  Click (Named $m "With Elin*"); Start-Sleep 1
  "pid $($p.Id) : $(Texts (Main $p.Id))"
  $i = Pick $m "world_lab"
  Check "mode With Elin, world_lab choisi (rang $i)" ("$i" -ne "-1" -and (Texts (Main $p.Id)) -match "No game window")
  Click (Named $m "Start"); Start-Sleep 3
  Check "Start : Startingâ€¦" ((State (Main $p.Id)) -match "^Starting")
  $run = $false; 1..90 | ForEach-Object { if (-not $run) { Start-Sleep 2; $run = (State (Main $p.Id)) -eq "Running" } }
  Check "le serveur arrive a Running" $run
  "    fenetre : $(Texts (Main $p.Id))"
  "    Elin : $((Get-Process Elin -ErrorAction SilentlyContinue | ForEach-Object { $_.Id }) -join ',')"
  [void][W]::PostMessage([IntPtr]$m.Current.NativeWindowHandle, 0x10, [IntPtr]::Zero, [IntPtr]::Zero); Start-Sleep 1
  $t = Answer $p.Id 7; "    boite : $t"
  Check "fermer la fenetre : la boite demande, No : toujours Running" ($t -match "The server is running" -and (State (Main $p.Id)) -eq "Running" -and -not $p.HasExited)
  Click (Named $m "Stop"); Start-Sleep 3
  $s = State (Main $p.Id); "    etat : $s"
  Check "Stop : Stopping: savingâ€¦ (ou deja Stopped)" ($s -match "^(Stopping|Stopped)")
  $stopped = $false; 1..30 | ForEach-Object { if (-not $stopped) { Start-Sleep 2; $stopped = (State (Main $p.Id)) -eq "Stopped" } }
  Check "puis Stopped, plus d'Elin" ($stopped -and -not (Get-Process Elin -ErrorAction SilentlyContinue))
  "    fenetre : $(Texts (Main $p.Id))"
  [void][W]::PostMessage([IntPtr]$m.Current.NativeWindowHandle, 0x10, [IntPtr]::Zero, [IntPtr]::Zero); Start-Sleep 2
  Check "ferme sans question" $p.HasExited
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
}
"`n$($script:ok)/$($script:ok + $script:ko) verifications OK"



