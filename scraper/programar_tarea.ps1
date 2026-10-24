# Registra la descarga diaria en el Programador de tareas de Windows.
# Uso (PowerShell, desde la raíz del repo):  powershell -ExecutionPolicy Bypass -File scraper\programar_tarea.ps1
# Para quitarla:  Unregister-ScheduledTask -TaskName "DepaRent descarga diaria" -Confirm:$false
param(
    [string]$Hora = "07:00"
)

$repo = Split-Path -Parent $PSScriptRoot
$script = Join-Path $PSScriptRoot "descarga_diaria.py"
$log = Join-Path $repo "data_diaria\ultima_ejecucion.log"
$py = (Get-Command py -ErrorAction Stop).Source

New-Item -ItemType Directory -Force (Join-Path $repo "data_diaria") | Out-Null

$accion = New-ScheduledTaskAction -Execute "cmd.exe" `
    -Argument "/c `"`"$py`" -3 -I `"$script`" > `"$log`" 2>&1`"" `
    -WorkingDirectory $repo
$disparador = New-ScheduledTaskTrigger -Daily -At $Hora
# StartWhenAvailable: si la PC estaba apagada a la hora, corre apenas se encienda.
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName "DepaRent descarga diaria" -Action $accion -Trigger $disparador `
    -Settings $ajustes -Description "Descarga diaria de anuncios de alquiler (scraper/descarga_diaria.py)" -Force | Out-Null

Write-Host "Tarea registrada: todos los dias a las $Hora. Salida en $log"
