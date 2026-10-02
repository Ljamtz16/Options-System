$names=@(
  'SPY Options Snapshot Collector',
  'SPY Options Prospective Dataset Builder',
  'Intraday Options Universe Collector',
  'Intraday Options Dataset Builder'
)
foreach($n in $names){
  $t=Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
  if($t){Disable-ScheduledTask -TaskName $n | Out-Null; Write-Output "DISABLED $n"}
}
Write-Output 'Local collectors disabled. Do this only after VPS timers are verified.'
