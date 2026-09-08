#requires -Version 7.0
<#
.SYNOPSIS
Configura AWS SES entrada por entrada en GitHub Auth. Sin -Apply verifica presencia.
.DESCRIPTION
Enter conserva variables existentes. PowerShell pide secretos con entrada oculta y cierra stdin de gh al enviarlos.
No guarda credenciales en archivos, no despliega y no envia correo.
.EXAMPLE
pwsh -File ./scripts/Set-AwsSesEnvironment.ps1 -Apply
#>
[CmdletBinding()]
param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$repository = 'MexIngSof/API.PY.DJANGO.Auth'
$environment = 'staging-pro-deploy'
$variables = @('AUTH_AWS_SES_REGION_NAME','AUTH_AWS_SES_FROM_EMAIL','AUTH_EMAIL_RETURN_PATH','AUTH_EMAIL_PROVIDER')
$secrets = @('AUTH_AWS_SES_ACCESS_KEY_ID','AUTH_AWS_SES_SECRET_ACCESS_KEY')
function Invoke-GhChecked([string[]]$Arguments) {
    $result = & gh @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI fallo: operacion incompleta. Corrige acceso/conectividad y vuelve a ejecutar.' }
    $result
}
function Get-Names([string]$Kind) {
    $json = Invoke-GhChecked @($Kind,'list','--repo',$repository,'--env',$environment,'--json','name')
    @((($json -join "`n") | ConvertFrom-Json) | ForEach-Object name)
}
Get-Command gh -ErrorAction Stop | Out-Null
Invoke-GhChecked @('api',"repos/$repository/environments/$environment",'--silent') | Out-Null
Write-Host "Destino: $repository / $environment"
$presentVariables = @(Get-Names 'variable')
$presentSecrets = @(Get-Names 'secret')
if ($Apply) {
    foreach ($name in $variables) {
        $value = Read-Host "$name (Enter conserva/omite; proveedor debe ser ses)"
        if ([string]::IsNullOrWhiteSpace($value)) {
            if ($name -notin $presentVariables -and $name -ne 'AUTH_EMAIL_RETURN_PATH') { throw "Falta valor obligatorio: $name" }
            continue
        }
        $value = $value.Trim()
        if ($value -match '[\r\n\x00]') { throw "Valor multilinea invalido: $name" }
        if ($name -eq 'AUTH_EMAIL_PROVIDER' -and $value -cne 'ses') { throw 'AUTH_EMAIL_PROVIDER debe ser ses.' }
        Invoke-GhChecked @('variable','set',$name,'--repo',$repository,'--env',$environment,'--body',$value) | Out-Null
        Write-Host "CONFIGURADO: $name"
    }
    foreach ($name in $secrets) {
        if ($name -in $presentSecrets) {
            $answer = Read-Host "$name existe. Escribe ACTUALIZAR para reemplazarlo; Enter conserva"
            if ($answer -ne 'ACTUALIZAR') { continue }
        }
        $secure = Read-Host "Introduce $name (entrada oculta; termina con Enter)" -AsSecureString
        $pointer = [IntPtr]::Zero
        $process = $null
        try {
            if ($secure.Length -eq 0) { throw "El secreto no puede estar vacio: $name" }
            $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
            if ($plain -match '[\r\n\x00]' -or $plain -match '\s') { throw "El secreto contiene espacios o saltos de linea: $name" }
            $start = [Diagnostics.ProcessStartInfo]::new()
            $start.FileName = (Get-Command gh -CommandType Application).Source
            $start.UseShellExecute = $false
            $start.CreateNoWindow = $true
            $start.RedirectStandardInput = $true
            foreach ($argument in @('secret','set',$name,'--repo',$repository,'--env',$environment)) {
                $start.ArgumentList.Add($argument)
            }
            $process = [Diagnostics.Process]::Start($start)
            $process.StandardInput.Write($plain)
            $process.StandardInput.Close()
            Write-Host "Guardando $name en GitHub..."
            if (-not $process.WaitForExit(60000)) {
                $process.Kill($true)
                throw "GitHub no respondio en 60 segundos. Verifica presencia antes de reintentar: $name"
            }
            if ($process.ExitCode -ne 0) { throw "No se pudo guardar $name en GitHub." }
        } finally {
            $plain = $null
            if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
            $secure.Dispose()
            if ($null -ne $process) { $process.Dispose() }
        }
        Write-Host "CONFIGURADO: $name"
    }
}
$presentVariables = @(Get-Names 'variable')
$presentSecrets = @(Get-Names 'secret')
$missing = @()
foreach ($name in ($variables + $secrets)) {
    $present = if ($name -in $secrets) { $name -in $presentSecrets } else { $name -in $presentVariables }
    $optional = $name -eq 'AUTH_EMAIL_RETURN_PATH'
    if (-not $present -and -not $optional) { $missing += $name }
    Write-Host ($name + ': ' + $(if($present){'PRESENTE'}elseif($optional){'OPCIONAL_OMITIDO'}else{'FALTA'}))
}
if ($missing.Count) { throw "Configuracion incompleta: $($missing -join ', ')" }
$provider = Invoke-GhChecked @('variable','get','AUTH_EMAIL_PROVIDER','--repo',$repository,'--env',$environment)
if (($provider -join '').Trim() -cne 'ses') { throw 'AUTH_EMAIL_PROVIDER no esta configurado como ses.' }
Write-Host 'PRESENCIA_VERIFICADA: no certifica credenciales AWS, despliegue ni envio real.'


