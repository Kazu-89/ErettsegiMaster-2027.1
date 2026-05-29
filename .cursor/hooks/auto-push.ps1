# Automatikus GitHub push hook.
# Amikor az agent befejez egy munkat, ez a script commitol es feltolti a valtozasokat,
# de CSAK akkor, ha tenylegesen volt modositas.

$ErrorActionPreference = "Stop"

# stdin JSON beolvasasa (a stop hook kuld adatot, de itt nem hasznaljuk)
$null = [Console]::In.ReadToEnd()

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
& $git add -A
& $git commit -m "auto: kod frissitese Cursorbol ($timestamp)" | Out-Null
& $git push 2>&1 | Out-Null

Write-Output '{}'
exit 0
