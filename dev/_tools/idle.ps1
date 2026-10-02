Add-Type @"
using System; using System.Runtime.InteropServices;
public static class Idle { [StructLayout(LayoutKind.Sequential)] struct LII { public uint cbSize; public uint dwTime; }
[DllImport("user32.dll")] static extern bool GetLastInputInfo(ref LII p);
public static double Seconds() { var l = new LII(); l.cbSize = (uint)Marshal.SizeOf(l); GetLastInputInfo(ref l); return (Environment.TickCount - l.dwTime) / 1000.0; } }
"@
[Idle]::Seconds()
