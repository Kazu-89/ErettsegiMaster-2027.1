# Automatikus GitHub push hook hibaellenorzessel.
#
# Amikor az agent befejez egy munkat:
#   1) vegigfut a Python kodon (szintaktikai / fordithatosagi ellenorzes),
#   2) ha HIBAT talal -> NEM pushol, hanem visszajelez, hogy javitani kell,
#   3) ha minden rendben es van valtozas -> commitol es feltolti GitHubra.
#
# Megjegyzes: a git/python a normal informacios uzeneteit a stderr-re irja,
# ezert NEM allitunk be "Stop" hibakezelest.

$ErrorActionPreference = "Continue"

# stdin JSON beolvasasa (a stop hook kuld adatot, de itt nem hasznaljuk)
try { $null = [Console]::In.ReadToEnd() } catch {}

$git = "C:\Program Files\Git\cmd\git.exe"
if (-not (Test-Path $git)) { $git = "git" }

$python = "python"

# Projekt gyoker (a script a .cursor/hooks mappaban van)
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $projectRoot

# Van-e egyaltalan valtozas? Ha nincs, nincs teendo.
$changes = & $git status --porcelain
if (-not $changes) {
    Write-Output '{}'
    exit 0
}

# --- Hibaellenorzes: minden .py fajl leforditasa (a .venv es data mappak nelkul) ---
$pyFiles = Get-ChildItem -Path $projectRoot -Recurse -Filter *.py -File |
    Where-Object { $_.FullName -notmatch '\\\.venv\\' -and $_.FullName -notmatch '\\data\\' }

$errors = @()
foreach ($file in $pyFiles) {
    $output = & $python -m py_compile $file.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        $errors += "$($file.Name): $output"
    }
}

if ($errors.Count -gt 0) {
    $joined = ($errors -join " | ")
    $msg = "A push KIMARADT, mert a kod hibat tartalmaz (nem fordul le): $joined Eloszor javitsd a hibat, aztan tortenik a feltoltes."
    $payload = @{ followup_message = $msg } | ConvertTo-Json -Compress
    Write-Output $payload
    exit 0
}

# --- Minden rendben: commit + push ---
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
& $git add -A 2>&1 | Out-Null
& $git commit -m "auto: kod frissitese Cursorbol ($timestamp)" 2>&1 | Out-Null
& $git push 2>&1 | Out-Null

Write-Output '{}'
exit 0
