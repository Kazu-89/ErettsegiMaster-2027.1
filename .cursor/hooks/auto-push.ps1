# Automatikus GitHub push hook.
# Amikor az agent befejez egy munkat, ez a script commitol es feltolti a valtozasokat,
# de CSAK akkor, ha tenylegesen volt modositas.
#
# Megjegyzes: a git a normal informacios uzeneteit a stderr-re irja, ezert NEM
# allitunk be "Stop" hibakezelest, kulonben a sikeres push is hibanak latszana.

$ErrorActionPreference = "Continue"

# stdin JSON beolvasasa (a stop hook kuld adatot, de itt nem hasznaljuk)
try { $null = [Console]::In.ReadToEnd() } catch {}

$git = "C:\Program Files\Git\cmd\git.exe"
if (-not (Test-Path $git)) {
    $git = "git"
}

# Projekt gyoker (a script a .cursor/hooks mappaban van)
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $projectRoot

# Van-e valtozas?
$changes = & $git status --porcelain
if (-not $changes) {
    Write-Output '{}'
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
& $git add -A 2>&1 | Out-Null
& $git commit -m "auto: kod frissitese Cursorbol ($timestamp)" 2>&1 | Out-Null
& $git push 2>&1 | Out-Null

Write-Output '{}'
exit 0
