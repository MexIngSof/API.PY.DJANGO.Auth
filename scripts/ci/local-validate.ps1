[CmdletBinding()]
param(
    [ValidateSet('fast','full','release')]
    [string]$Mode = 'fast'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $root
try {
    function Assert-Command([string]$Name) {
        if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
            throw "BLOCKED: required command '$Name' is not available"
        }
    }

    $requiredFiles = @('manage.py','requirements.txt','service-metadata.yml')
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path -LiteralPath $file)) { throw "FAIL: missing required file $file" }
    }

    $metadata = Get-Content service-metadata.yml -Raw
    if ($metadata -notmatch 'framework_policy_version:\s*["'']2026\.09\.3["'']') {
        throw 'FAIL: service-metadata.yml is not on framework policy 2026.09.3'
    }
    if ($metadata -notmatch 'deploy_authority_branch:\s*pro') {
        throw 'FAIL: deployment authority must remain pro'
    }

    if (Test-Path '.github/workflows') {
        foreach ($workflow in Get-ChildItem '.github/workflows' -File -Filter '*.yml') {
            $text = Get-Content $workflow.FullName -Raw
            foreach ($trigger in @('push:', 'pull_request:', 'pull_request_target:', 'merge_group:', 'schedule:', 'workflow_run:', 'repository_dispatch:')) {
                if ($text -match "(?m)^\s*$([regex]::Escape($trigger))") {
                    throw "FAIL: hosted workflow $($workflow.Name) contains forbidden automatic trigger $trigger"
                }
            }
            if ($text -notmatch 'workflow_dispatch') { throw "FAIL: hosted workflow $($workflow.Name) is not manual dispatch" }
            if ($text -notmatch "refs/heads/pro") { throw "FAIL: hosted workflow $($workflow.Name) is not restricted to pro" }
        }
    }

    Assert-Command python
    python -m compileall -q .
    if ($LASTEXITCODE -ne 0) { throw 'FAIL: Python compile validation failed' }

    if ($Mode -in @('full','release')) {
        python manage.py check
        if ($LASTEXITCODE -ne 0) { throw 'FAIL: django check failed' }
        python manage.py makemigrations --check --dry-run
        if ($LASTEXITCODE -ne 0) { throw 'FAIL: migration drift detected' }
        python manage.py test
        if ($LASTEXITCODE -ne 0) { throw 'FAIL: test suite failed' }
        python -m pip check
        if ($LASTEXITCODE -ne 0) { throw 'FAIL: pip dependency check failed' }
    }

    if ($Mode -eq 'release') {
        Assert-Command docker
        docker build --check -f Dockerfile .
        if ($LASTEXITCODE -ne 0) { throw 'FAIL: Docker build check failed' }
        if (Get-Command trivy -ErrorAction SilentlyContinue) {
            trivy fs --exit-code 1 --severity CRITICAL --ignore-unfixed .
            if ($LASTEXITCODE -ne 0) { throw 'FAIL: Trivy filesystem scan failed' }
        } else {
            throw 'BLOCKED: release validation requires trivy for the local vulnerability/secret gate'
        }
    }

    [pscustomobject]@{
        Status = 'PASS'
        Mode = $Mode
        FrameworkPolicy = '2026.09.3'
        Repository = 'MexIngSof/API.PY.DJANGO.Auth'
    }
}
finally {
    Pop-Location
}
