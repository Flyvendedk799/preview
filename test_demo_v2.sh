#!/bin/bash
# Test demo-v2 job flow (Linux/macOS)
# Usage: ./test_demo_v2.sh [base_url]
# Default base_url: https://www.mymetaview.com

BASE_URL="${1:-https://www.mymetaview.com}"
API="${BASE_URL}/api/v1/demo-v2"
TEST_URLS=("https://subpay.dk/" "https://stripe.com/" "https://futurematch.dk/")

echo "=== Demo-v2 Job Flow Test ==="
echo "API base: $API"
echo ""

for url in "${TEST_URLS[@]}"; do
  echo "--- Testing: $url ---"
  
  # Create job
  RESP=$(curl -s -X POST "$API/jobs" -H "Content-Type: application/json" -d "{\"url\":\"$url\"}")
  JOB_ID=$(echo "$RESP" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
  
  if [ -z "$JOB_ID" ]; then
    echo "  FAIL: Could not create job. Response: $RESP"
    continue
  fi
  echo "  Job ID: $JOB_ID"
  
  # Poll
  for i in {1..60}; do
    sleep 2
    STATUS=$(curl -s "$API/jobs/$JOB_ID/status")
    S=$(echo "$STATUS" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    P=$(echo "$STATUS" | grep -o '"progress":[0-9.]*' | cut -d':' -f2)
    echo "  [$i] status=$S progress=$P"
    
    if [ "$S" = "finished" ]; then
      TITLE=$(echo "$STATUS" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)
      echo "  SUCCESS: $TITLE"
      break
    fi
    if [ "$S" = "failed" ]; then
      ERR=$(echo "$STATUS" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
      echo "  FAILED: $ERR"
      break
    fi
  done
  echo ""
done

echo "=== Test Complete ==="
