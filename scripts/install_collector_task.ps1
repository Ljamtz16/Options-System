$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c "D:\Proyectos\Raspberry\Options System\scripts\run_collector.cmd"'
$Trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
$Trigger.Repetition = (New-ScheduledTaskTrigger -Once -At "09:00" -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Hours 14)).Repetition
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "SPY Options Snapshot Collector" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Point-in-time SPY options research snapshots; script stores only while Alpaca market clock is open." -Force
