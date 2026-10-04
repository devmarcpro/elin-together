# Compile ElinTogetherServer.exe avec le compilateur C# livre avec Windows (.NET Framework 4) : rien a installer,
# aucune dependance, un fichier de quelques dizaines de Ko. Sortie : dev\_release\template\ElinTogetherServer.exe
$ErrorActionPreference = 'Stop'
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$out = Join-Path $PSScriptRoot '..\_release\template\ElinTogetherServer.exe'
& $csc /nologo /target:winexe /optimize+ "/out:$out" /r:System.Windows.Forms.dll /r:System.Drawing.dll (Join-Path $PSScriptRoot 'ElinTogetherServer.cs')
if ($LASTEXITCODE -ne 0) { exit 1 }
"{0} ({1} octets)" -f (Resolve-Path $out), (Get-Item $out).Length
