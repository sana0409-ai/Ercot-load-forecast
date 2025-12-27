<#
Start the FastAPI app on port 8001 with logs captured.
Usage: .\run_server_8001.ps1
#>

param(
    [int]$Port = 8001,
    [string]$ServerHost = '127.0.0.1'
)

$uvOut = ".\uvicorn_out_$Port.log"
$uvErr = ".\uvicorn_err_$Port.log"

# Best-effort: stop any process listening on the port
try {
    $pids = (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).OwningProcess | Sort-Object -Unique
    foreach ($pp in $pids) {
        Write-Output "Stopping pid $pp"
        Stop-Process -Id $pp -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Warning ("Could not stop processes on port {0}: {1}" -f $Port, $_)
}

Remove-Item $uvOut, $uvErr -ErrorAction SilentlyContinue

$args = "-m uvicorn main:app --host $ServerHost --port $Port"
Start-Process -NoNewWindow -FilePath 'python' -ArgumentList $args -RedirectStandardOutput $uvOut -RedirectStandardError $uvErr

Write-Output "Started uvicorn on http://$ServerHost`:$Port"
Write-Output "Logs: $uvOut , $uvErr"
