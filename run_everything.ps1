[CmdletBinding()]
param(
    # Cenarios criticos: all|catastrofe|degradacao|rajadas|indisponibilidade|normal
    [ValidateSet('all','catastrofe','degradacao','rajadas','indisponibilidade','normal')]
    [string]$Scenarios = 'all',

    # Se definido, pula o "cenario-completo" (V1/V2)
    [switch]$SkipCompleteScenario,

    # Se definido, nao roda a parte estatistica / charts academicos
    [switch]$SkipAcademic
)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Require-Command([string]$Name, [string]$Hint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando '$Name' não encontrado. $Hint"
    }
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ArgumentList
    )

    $displayArgs = ''
    if ($null -ne $ArgumentList -and $ArgumentList.Count -gt 0) {
        $displayArgs = ($ArgumentList -join ' ')
    }

    $suffix = ''
    if ($displayArgs) {
        $suffix = " $displayArgs"
    }

    Write-Host ("> $FilePath$suffix") -ForegroundColor DarkGray

    if ($null -eq $ArgumentList -or $ArgumentList.Count -eq 0) {
        & $FilePath
    } else {
        & $FilePath @ArgumentList
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Falhou: $FilePath (exit code $LASTEXITCODE)"
    }
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Pipeline completa (tests + cenários + análises + plots)" -ForegroundColor Green
Write-Host "Root: $projectRoot" -ForegroundColor DarkGray

# Por padrao, inclui V3 (Retry/Backoff) nos scripts bash que suportam.
$env:INCLUDE_V3 = 'true'

# Pré-requisitos básicos
Require-Command 'docker' 'Instale o Docker Desktop e garanta que o docker está no PATH.'
Require-Command 'python' 'Instale Python 3.x e garanta que o python está no PATH.'
Require-Command 'bash' 'Instale Git for Windows (Git Bash) ou WSL, para executar os scripts .sh.'

Write-Step 'Checando Docker'
try {
    docker info | Out-Null
} catch {
    throw "Docker não parece estar rodando. Inicie o Docker Desktop e tente novamente. Detalhe: $($_.Exception.Message)"
}

Write-Step 'Preparando virtualenv Python (.venv)'
if (-not (Test-Path -Path '.venv')) {
    Invoke-External 'python' @('-m','venv','.venv')
}

# Ativa venv (PowerShell)
$activate = Join-Path $projectRoot '.venv\Scripts\Activate.ps1'
if (-not (Test-Path $activate)) {
    throw "Não achei o activate do venv em: $activate. Apague a pasta .venv e rode de novo."
}
. $activate

Write-Step 'Instalando dependências Python'
Invoke-External 'python' @('-m','pip','install','-U','pip')
Invoke-External 'python' @('-m','pip','install','-r','requirements.txt')

# 1) Cenário completo (V1/V2) + análise baseline
if (-not $SkipCompleteScenario) {
    Write-Step 'Executando cenário completo (V1 e V2)'
    Invoke-External 'bash' @('./run_all_tests.sh')

    Write-Step 'Analisando cenário completo (gera analysis_results/*)'
    Invoke-External 'python' @('analysis/scripts/analyzer.py')
}

# 2) Cenários críticos + análise por cenário
Write-Step "Executando cenários críticos (Scenarios=$Scenarios)"
Invoke-External 'bash' @('./run_scenario_tests.sh', $Scenarios)

Write-Step 'Analisando cenários críticos (relatórios + plots)'
if ($Scenarios -eq 'all') {
    Invoke-External 'python' @('analysis/scripts/scenario_analyzer.py')
} else {
    Invoke-External 'python' @('analysis/scripts/scenario_analyzer.py', $Scenarios)
}

Write-Step 'Gerando gráficos consolidados finais (final_charts)'
Invoke-External 'python' @('analysis/scripts/generate_final_charts.py')

# 3) Estatística + charts acadêmicos
if (-not $SkipAcademic) {
    Write-Step 'Análise estatística (statistics)'
    Invoke-External 'python' @('analysis/scripts/statistical_analysis.py', '--data-dir', 'analysis_results', '--output-dir', 'analysis_results/statistics', '--validate')

    Write-Step 'Gráficos acadêmicos (academic_charts)'
    Invoke-External 'python' @('analysis/scripts/generate_academic_charts.py', '--data-dir', 'analysis_results', '--output-dir', 'analysis_results/academic_charts', '--demo')
}

Write-Host "`nOK. Artefatos gerados:" -ForegroundColor Green
Write-Host "- analysis_results/analysis_report.html" -ForegroundColor Gray
Write-Host "- analysis_results/scenarios/*_report.html" -ForegroundColor Gray
Write-Host "- analysis_results/final_charts/*.png" -ForegroundColor Gray
Write-Host "- analysis_results/academic_charts/*" -ForegroundColor Gray
Write-Host "- analysis_results/statistics/*" -ForegroundColor Gray
