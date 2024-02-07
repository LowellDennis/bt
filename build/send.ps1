Param(
  [string]$to,
  [string]$subject,
  [string]$message
)

$outlook = New-Object -com Outlook.Application
$mail = $outlook.CreateItem(0)
$mail.importance = 2
$mail.subject = $subject
$mail.body = $message
$mail.To = $to
$username = Get-Item Env:USERNAME
$mail.Sender = $username.value + "@hpe.com"
$mail.Send()
