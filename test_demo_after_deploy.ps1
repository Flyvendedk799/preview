# Test script to wait for Railway deployment and test demo-v2 endpoint
# Uses async job flow: POST /jobs -> poll GET /jobs/{id}/status
Write-Host "Waiting 300 seconds for Railway deployment..."
Start-Sleep -Seconds 300

Write-Host "`n=== Starting Demo-v2 Test ===" -ForegroundColor Green
Write-Host "Time: $(Get-Date)" -ForegroundColor Cyan

# Test URLs - subpay.dk, stripe.com, futurematch.dk per AIL-33
$testUrls = @("https://subpay.dk/", "https://stripe.com/", "https://futurematch.dk/")
$apiBase = "https://www.mymetaview.com/api/v1/demo-v2"

foreach ($testUrl in $testUrls) {
    Write-Host "`n--- Testing: $testUrl ---" -ForegroundColor Yellow
    
    try {
        # 1. Create job
        $createUrl = "$apiBase/jobs"
        $body = @{ url = $testUrl } | ConvertTo-Json
        Write-Host "Creating job..." -ForegroundColor Cyan
        $createResponse = Invoke-RestMethod -Uri $createUrl -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
        
        $jobId = $createResponse.job_id
        Write-Host "Job created: $jobId" -ForegroundColor Cyan
        
        # 2. Poll for completion (max 2 min)
        $statusUrl = "$apiBase/jobs/$jobId/status"
        $maxAttempts = 60
        $attempt = 0
        
        while ($attempt -lt $maxAttempts) {
            Start-Sleep -Seconds 2
            $statusResponse = Invoke-RestMethod -Uri $statusUrl -Method Get -ErrorAction Stop
            
            Write-Host "  Status: $($statusResponse.status) | Progress: $($statusResponse.progress)" -ForegroundColor Gray
            
            if ($statusResponse.status -eq "finished") {
                Write-Host "  SUCCESS! Title: $($statusResponse.result.title)" -ForegroundColor Green
                break
            }
            if ($statusResponse.status -eq "failed") {
                Write-Host "  FAILED: $($statusResponse.error)" -ForegroundColor Red
                break
            }
            
            $attempt++
        }
        
        if ($attempt -ge $maxAttempts) {
            Write-Host "  TIMEOUT after 2 minutes" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "Check Railway logs for: 'AI', 'banding', 'gradient', 'quality', 'error'" -ForegroundColor Cyan
