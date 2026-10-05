[CmdletBinding()]
param([ValidateSet('fast','full','release')][string]$Mode='fast')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $root
try {
  Write-Host '==> STATIC_CONTRACT'
  foreach($file in @('manage.py','user/models.py','user/migrations/0006_application_scoped_email_identity.py','user/application_scope.py','user/account_scope.py','user/scoped_views.py','auth/custom_email.py','auth/tests/test_application_email_identity_preflight.py','auth/tests/test_application_scoped_refresh.py','auth/tests/test_application_scoped_session_revocation.py','auth/tests/test_application_scoped_password_change.py','auth/tests/test_reset_password_confirm_application_scope.py','auth/tests/test_email_trusted_application_context.py','auth/tests/test_application_email_template_fallback.py','auth/tests/test_email_sender_fallback_contract.py','auth/tests/test_email_branding_fallback_contract.py','auth/tests/test_global_identity_contract.py')) { if(-not(Test-Path -LiteralPath $file)){throw "STATIC_CONTRACT_FAILURE: missing required file $file"} }
  $userModel=Get-Content user/models.py -Raw
  if($userModel -match 'email\s*=\s*models\.EmailField\([^\r\n]*unique=True'){throw 'STATIC_CONTRACT_FAILURE: Task 5 forbids global email uniqueness'}
  foreach($token in @('UniqueConstraint','fields=("idApp", "email")','uq_useraccounts_application_email')){if($userModel -notmatch [regex]::Escape($token)){throw "STATIC_CONTRACT_FAILURE: Task 5 application email contract missing: $token"}}
  $scope=Get-Content user/application_scope.py -Raw
  foreach($token in @('X-Application-Code','X-Gateway-Internal-Token','APPLICATION_CONTEXT_MISMATCH','GATEWAY_CONTEXT_REQUIRED','APPLICATION_CODE_REQUIRED')){if($scope -notmatch [regex]::Escape($token)){throw "STATIC_CONTRACT_FAILURE: trusted context missing: $token"}}

  if(-not(Get-Command python -ErrorAction SilentlyContinue)){throw 'DEPENDENCY_BLOCKED: python unavailable'}
  Write-Host '==> PYTHON_COMPILE'
  python -m compileall -q . -x '(^|/)(\.git|\.venv|venv|node_modules)/'
  if($LASTEXITCODE -ne 0){throw 'PYTHON_COMPILE failed'}

  if($Mode -in @('full','release')){
    Write-Host '==> DJANGO_CHECK'; python manage.py check; if($LASTEXITCODE -ne 0){throw 'DJANGO_CHECK failed'}
    Write-Host '==> MIGRATION_CHECK'; python manage.py makemigrations --check --dry-run; if($LASTEXITCODE -ne 0){throw 'MIGRATION_CHECK failed'}
    Write-Host '==> FOCUSED_TESTS'
    python manage.py test auth.tests.test_application_email_identity_preflight auth.tests.test_application_scoped_refresh auth.tests.test_application_scoped_session_revocation auth.tests.test_application_scoped_password_change auth.tests.test_reset_password_confirm_application_scope auth.tests.test_email_trusted_application_context auth.tests.test_application_email_template_fallback auth.tests.test_email_sender_fallback_contract auth.tests.test_email_branding_fallback_contract auth.tests.test_global_identity_contract -v 2
    if($LASTEXITCODE -ne 0){throw 'FOCUSED_TESTS failed'}
    Write-Host '==> FULL_TESTS'; python manage.py test -v 2; if($LASTEXITCODE -ne 0){throw 'FULL_TESTS failed'}
    Write-Host '==> POSTGRES_OWNER_CERTIFICATION'; python scripts/certify_erp_client_platform.py; if($LASTEXITCODE -ne 0){throw 'POSTGRES_OWNER_CERTIFICATION failed'}
  }
  [pscustomobject]@{Status='PASS';Mode=$Mode;StaticContract='PASS';Runtime=if($Mode -eq 'fast'){'RUNTIME_VERIFICATION_REQUIRED'}else{'OBSERVED_BY_THIS_RUN'}}
} finally {Pop-Location}
