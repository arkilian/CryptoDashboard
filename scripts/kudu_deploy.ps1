# Deploy direto via Kudu ZIP Deploy API

Write-Host "Obtendo credenciais de publishing..."
$credsJson = az webapp deployment list-publishing-credentials `
    --name arkilian-webapp `
    --resource-group arkilian-group `
    --query '{username:publishingUserName,password:publishingPassword}' `
    -o json | ConvertFrom-Json

$username = $credsJson.username
$password = $credsJson.password

# Base64 encode credentials
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$($username):$($password)"))

# Kudu endpoint
$url = "https://arkilian-webapp-def7evcab7gghrfn.scm.francecentral-01.azurewebsites.net/api/zip/site/wwwroot"

Write-Host "Deploying deploy.zip to $url..."

$headers = @{
    Authorization = "Basic $base64AuthInfo"
}

try {
    $response = Invoke-WebRequest -Uri $url `
        -Method Put `
        -Headers $headers `
        -InFile "deploy.zip" `
        -ContentType "application/zip" `
        -TimeoutSec 600 `
        -UseBasicParsing
    
    Write-Host "✅ Deploy successful! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host $response.Content
} catch {
    Write-Host "❌ Deploy failed!" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)"
    Write-Host "Message: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host "Response: $($reader.ReadToEnd())"
    }
    exit 1
}
