Param(
  [string]$to,
  [string]$subject,
  [string]$message
)

# Ensure Microsoft.Graph is installed
if (-not (Get-Module -ListAvailable -Name Microsoft.Graph)) {
    Install-Module Microsoft.Graph -Scope CurrentUser -Force
}

# Connect to Microsoft Graph (first run will prompt for login)
Connect-MgGraph -NoWelcome -Scopes "Mail.Send"

# Get the signed-in user ID (UPN)
$user = (Get-MgContext).Account

# Send the email
Send-MgUserMail -UserId $user -BodyParameter @{
    Message = @{
        Subject = $subject
        Body = @{
            ContentType = "Text"
            Content = $message
        }
        ToRecipients = @(
            @{
                EmailAddress = @{
                    Address = $to
                }
            }
        )
    }
    SaveToSentItems = "true"
}
