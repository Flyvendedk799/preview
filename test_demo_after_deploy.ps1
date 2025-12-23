# Test script to wait for Railway deployment and test demo endpoint
Write-Host "Waiting 300 seconds for Railway deployment..."
Start-Sleep -Seconds 300

Write-Host "`n=== Starting Demo Test ===" -ForegroundColor Green
Write-Host "Time: $(Get-Date)" -ForegroundColor Cyan

# Test URL - using futurematch.dk which we've been testing
$testUrl = "https://futurematch.dk/"
$apiUrl = "https://www.mymetaview.com/api/v1/demo/preview"

Write-Host "`nTesting URL: $testUrl" -ForegroundColor Yellow
Write-Host "API Endpoint: $apiUrl" -ForegroundColor Yellow

try {
    $body = @{
        url = $testUrl
    } | ConvertTo-Json

    Write-Host "`nSending POST request..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
    
    Write-Host "`n✅ Test SUCCESS!" -ForegroundColor Green
    Write-Host "Job ID: $($response.job_id)" -ForegroundColor Cyan
    Write-Host "Status: $($response.status)" -ForegroundColor Cyan
    
    # Wait a bit for job to process
    Write-Host "`nWaiting 10 seconds for job to start processing..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
} catch {
    Write-Host "`n❌ Test FAILED!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "Check Railway logs for: 'AI', 'banding', 'gradient', 'quality', 'error'" -ForegroundColor Cyan

