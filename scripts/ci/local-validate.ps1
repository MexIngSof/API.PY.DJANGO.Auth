[CmdletBinding()]
param(
    [ValidateSet('fast','full','release')]
    [string]$Mode = 'fast'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$expectedPython = '3.13.15'
$expectedDjango = '5.2.17'
$expectedDrf = '3.17.2'
$expectedPsycopg = '3.2.13'
$expectedPostgres = '16.15'
$baseline = 'django-api-2026.09'
Push-Location $root
try {
    function Assert-Command([string]$Name) {
        if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
            throw "BLOCKED: required command '$Name' is not available"
        }
    }
    function Invoke-Checked([string]$Label, [scriptblock]$Command) {
        Write-Host "==> $Label"
        & $Command
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            throw "FAIL: $Label failed with exit code $LASTEXITCODE"
        }
    }
    function Assert-Contains([string]$Text,[string]$Pattern,[string]$Failure) {
        if ($Text -notmatch $Pattern) { throw $Failure }
    }

    foreach ($file in @('manage.py','requirements.txt','service-metadata.yml','Dockerfile','config/settings.py','config/asgi.py','config/observability.py','auth_health.py','config/urls.py','.env.local.example','scripts/certify_erp_client_platform.py')) {
        if (-not (Test-Path -LiteralPath $file)) { throw "FAIL: missing required file $file" }
    }

    $metadata = Get-Content service-metadata.yml -Raw
    foreach ($pattern in @(
        'framework_policy_version:\s*["'']2026\.09\.3["'']',
        'api_platform_baseline:\s*["'']django-api-2026\.09["'']',
        'api_platform_adoption_state:\s*CANDIDATE',
        'python:\s*["'']3\.13\.15["'']',
        'django:\s*["'']5\.2\.17["'']',
        'drf:\s*["'']3\.17\.2["'']',
        'engine:\s*postgresql',
        'deploy_authority_branch:\s*pro',
        'user_policy:\s*DB_USER_EQUALS_DB_NAME',
        'readiness_path:\s*/ready/',
        'command:\s*scripts/ci/local-validate\.ps1'
    )) {
        Assert-Contains $metadata $pattern "FAIL: Auth service metadata is not aligned with API platform baseline ($pattern)"
    }

    $requirements = Get-Content requirements.txt -Raw
    foreach ($token in @(
        'Django==5.2.17',
        'djangorestframework==3.17.2',
        'psycopg[binary]==3.2.13'
    )) {
        if ($requirements -notmatch [regex]::Escape($token)) { throw "FAIL: requirements target missing: $token" }
    }

    $dockerfile = Get-Content Dockerfile -Raw
    Assert-Contains $dockerfile 'FROM\s+python:3\.13\.15-slim-bookworm' 'FAIL: Docker Python 3.13.15 target missing'
    if ($dockerfile -match 'python -m pip install -r requirements\.txt\s+"uvicorn') {
        throw 'FAIL: Dockerfile must not install Uvicorn outside requirements.txt'
    }

    $certifier = Get-Content scripts/certify_erp_client_platform.py -Raw
    if ($certifier -match 'PostgreSQL 14\.4|140004') { throw 'FAIL: legacy PostgreSQL 14.4 certification target remains' }
    if ($certifier -notmatch 'PostgreSQL 16\.15' -or $certifier -notmatch '160015') {
        throw 'FAIL: PostgreSQL 16.15 certification target is missing'
    }

    $settings = Get-Content config/settings.py -Raw
    if ($settings -match 'django\.db\.backends\.sqlite3') { throw 'FAIL: SQLite is prohibited' }
    if ($settings -notmatch 'django\.db\.backends\.postgresql') { throw 'FAIL: PostgreSQL must be explicit' }
    if ($settings -notmatch 'search_path=.*public') { throw 'FAIL: PostgreSQL search_path must include public' }
    if ($settings -notmatch 'DB_USER == DB_NAME' -and $settings -notmatch 'config\.get\("NAME"\) != config\.get\("USER"\)') { throw 'FAIL: DB_USER == DB_NAME enforcement is missing' }

    $envText = Get-Content '.env.local.example' -Raw
    if ($envText -notmatch '(?m)^AUTH_DB_NAME=Auth\s*$' -or $envText -notmatch '(?m)^AUTH_DB_USER=Auth\s*$') { throw 'FAIL: canonical Auth DB identity is missing' }
    if ($envText -match '(?im)^\w*(DB_USER|POSTGRES_USER)=.*_user\s*$') { throw 'FAIL: legacy *_user database alias detected' }
    if ($envText -match '(?i)(change-me|replace-me|replace_with_|dev-[a-z0-9-]*secret|local-[a-z0-9-]*secret)') { throw 'FAIL: predictable placeholder secret detected' }

    $urls = Get-Content config/urls.py -Raw
    $health = Get-Content auth_health.py -Raw
    if ($urls -notmatch 'path\("health/"' -or $urls -notmatch 'path\("ready/"') { throw 'FAIL: health/readiness routes are required' }
    if ($health -notmatch 'connection\.ensure_connection\(\)' -or $health -notmatch 'status=503') { throw 'FAIL: readiness must verify database connectivity' }

    $asgi = Get-Content config/asgi.py -Raw
    $observability = Get-Content config/observability.py -Raw
    if ($asgi -notmatch 'ObservabilityMiddleware\(get_asgi_application\(\)\)') { throw 'FAIL: ASGI observability wrapper is required' }
    if ($observability -notmatch 'x-request-id' -or $observability -notmatch 'x-correlation-id' -or $observability -notmatch 'json\.dumps') { throw 'FAIL: canonical request IDs and JSON logging are required' }

    if (Test-Path '.github/workflows') {
        foreach ($workflow in Get-ChildItem '.github/workflows' -File | Where-Object Extension -in @('.yml','.yaml')) {
            $text = Get-Content $workflow.FullName -Raw
            if ($text -match '(?m)^\s*(push|pull_request|pull_request_target|merge_group|schedule|workflow_run|repository_dispatch):' -or $text -match '(?m)^\s*on:\s*\[[^\]]*(push|pull_request|schedule|workflow_run|repository_dispatch)') {
                throw "FAIL: hosted workflow $($workflow.Name) contains a forbidden automatic trigger"
            }
            if ($text -notmatch 'workflow_dispatch') { throw "FAIL: hosted workflow $($workflow.Name) is not manual dispatch" }
            if ($text -notmatch 'refs/heads/pro') { throw "FAIL: hosted workflow $($workflow.Name) is not restricted to pro" }
        }
    }

    Assert-Command git
    Invoke-Checked 'git diff --check' { git diff --check }
    Assert-Command python
    $pythonVersion = (& python -c 'import platform; print(platform.python_version())').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'BLOCKED: unable to inspect Python runtime' }
    if ($pythonVersion -ne $expectedPython) { throw "BLOCKED: Python $expectedPython required; found $pythonVersion" }

    Invoke-Checked 'Python compile validation' { python -m compileall -q . -x '(^|/)(\.git|\.venv|venv|node_modules)/' }

    if ($Mode -in @('full','release')) {
        Invoke-Checked 'pip dependency check' { python -m pip check }
        Invoke-Checked 'installed framework tuple' {
            python -c "import django,rest_framework,psycopg; assert django.get_version() == '$expectedDjango'; assert rest_framework.VERSION == '$expectedDrf'; assert psycopg.__version__ == '$expectedPsycopg'"
        }
        Invoke-Checked 'Django check' { python manage.py check }
        Invoke-Checked 'Django deploy check' { python manage.py check --deploy }
        Invoke-Checked 'migration drift check' { python manage.py makemigrations --check --dry-run }
        Invoke-Checked 'migration plan' { python manage.py migrate --plan }
        Invoke-Checked 'Django tests' { python manage.py test -v 2 }
        Invoke-Checked 'owner-local PostgreSQL certification' { python scripts/certify_erp_client_platform.py }
    }

    if ($Mode -eq 'release') {
        foreach ($tool in @('docker','trivy','syft')) { Assert-Command $tool }
        $tag = "local/auth-release-check:$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
        $sbom = Join-Path $env:TEMP "auth-sbom-$([guid]::NewGuid().ToString('N')).json"
        try {
            Invoke-Checked 'Docker build' { docker build --pull --file Dockerfile --tag $tag . }
            Invoke-Checked 'container version tuple' {
                docker run --rm --entrypoint python $tag -c "import platform,django,rest_framework,psycopg; assert platform.python_version() == '$expectedPython'; assert django.get_version() == '$expectedDjango'; assert rest_framework.VERSION == '$expectedDrf'; assert psycopg.__version__ == '$expectedPsycopg'"
            }
            Invoke-Checked 'Trivy vulnerability and secret scan' { trivy image --exit-code 1 --severity CRITICAL --scanners vuln,secret --ignore-unfixed $tag }
            Invoke-Checked 'SBOM generation' { syft $tag -o cyclonedx-json=$sbom }
            if (-not (Test-Path $sbom)) { throw 'FAIL: SBOM was not generated' }
        }
        finally {
            Remove-Item $sbom -Force -ErrorAction SilentlyContinue
            docker image rm $tag 2>$null | Out-Null
        }
    }

    [pscustomobject]@{
        Status = 'PASS'
        Mode = $Mode
        FrameworkPolicy = '2026.09.3'
        ApiPlatformBaseline = $baseline
        Python = $expectedPython
        Django = $expectedDjango
        DRF = $expectedDrf
        Psycopg = $expectedPsycopg
        PostgreSQLTarget = $expectedPostgres
        Repository = 'MexIngSof/API.PY.DJANGO.Auth'
    }
}
finally {
    Pop-Location
}
