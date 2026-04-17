$taskName  = "LeDeclicMental"
$batFile   = "C:\Users\LM131\Internship\lancer.bat"
$heure     = "08:00"

$action    = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batFile`""
$trigger   = New-ScheduledTaskTrigger -Daily -At $heure
$settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force

Write-Host ""
Write-Host "Tache planifiee installee avec succes !"
Write-Host "Le bot tournera tous les matins a $heure"
Write-Host ""
