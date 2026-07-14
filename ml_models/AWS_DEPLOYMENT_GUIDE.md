# CLARIQ PRODUCTION DEPLOYMENT GUIDE

## Overview

This guide walks you through deploying the Clariq ML system from local development to AWS production.

**Timeline:** 2-3 hours (first time)

**What you'll have:**
- ✅ Automated 12am daily inference
- ✅ Historical data comparison reports
- ✅ Autonomous task execution
- ✅ ROI tracking and proof
- ✅ Real-time notifications

---

## Prerequisites

- AWS Account (with CLI configured)
- Python 3.9+
- Git and GitHub access
- ~$20/month AWS cost

---

## STEP 1: Local Validation (15 minutes)

Before deploying to AWS, validate everything works locally.

```bash
# 1. Install dependencies
cd /Users/ebubeepuna/Downloads/clariq
pip install -r ml_models/requirements.txt

# 2. Run data pipeline test
python ml_models/data_pipeline.py
# Expected output: Report showing historical comparison, ROI analysis

# 3. Run complete test suite
python ml_models/local_test_suite.py
# Expected output: All 6 tests PASS, ready for AWS

# 4. Run AI agent POC
python ml_models/poc_demo.py
# Expected output: Full intelligence report with all 7 layers
```

**Success criteria:**
- ✓ All tests pass
- ✓ Reports generate without errors
- ✓ ROI proof shows 5-15x return
- ✓ Models save to disk

---

## STEP 2: AWS Infrastructure Setup (30 minutes)

### 2.1 Create S3 Buckets

```bash
# Create data bucket
aws s3 mb s3://clariq-data-prod --region us-east-1

# Create models bucket
aws s3 mb s3://clariq-ml-models-prod --region us-east-1

# Create reports bucket
aws s3 mb s3://clariq-reports-prod --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket clariq-data-prod \
  --versioning-configuration Status=Enabled
```

### 2.2 Create DynamoDB Tables

```bash
# Create inference history table
aws dynamodb create-table \
  --table-name clariq-inference-history \
  --attribute-definitions AttributeName=store_id,AttributeType=S \
  --key-schema AttributeName=store_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Create sellers table
aws dynamodb create-table \
  --table-name clariq-sellers \
  --attribute-definitions \
    AttributeName=store_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema AttributeName=store_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 2.3 Create IAM Role for Lambda

```bash
# Create trust policy
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name clariq-lambda-role \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name clariq-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name clariq-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
  --role-name clariq-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess

aws iam attach-role-policy \
  --role-name clariq-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

---

## STEP 3: Lambda Function Deployment (30 minutes)

### 3.1 Package Lambda Function

```bash
cd /Users/ebubeepuna/Downloads/clariq/ml_models

# Create deployment package
mkdir lambda_package
cd lambda_package

# Copy source files
cp ../aws_lambda_daily_inference.py .
cp ../data_pipeline.py .
cp ../clariq_ai_agent.py .

# Install dependencies
pip install -r ../requirements.txt -t .

# Create zip
zip -r ../lambda_function.zip .

# Verify
unzip -l ../lambda_function.zip | head -20
```

### 3.2 Create Lambda Function

```bash
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get role ARN
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/clariq-lambda-role"

# Wait for role to be available
sleep 10

# Create function
aws lambda create-function \
  --function-name clariq-daily-inference \
  --runtime python3.9 \
  --role "$ROLE_ARN" \
  --handler aws_lambda_daily_inference.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 900 \
  --memory-size 1024 \
  --environment Variables="{ \
    BUCKET=clariq-ml-models-prod, \
    REPORTS_PREFIX=reports, \
    TABLE_NAME=clariq-inference-history \
  }"

echo "✓ Lambda function created"
```

### 3.3 Test Lambda Locally

```bash
# Test the function
aws lambda invoke \
  --function-name clariq-daily-inference \
  --payload '{}' \
  /tmp/lambda-response.json

cat /tmp/lambda-response.json
# Expected: {"statusCode": 200, "body": {...}}
```

---

## STEP 4: EventBridge Scheduling (15 minutes)

### 4.1 Create EventBridge Rule for 12am Daily

```bash
# Create rule that triggers at 12:00 AM UTC daily
aws events put-rule \
  --name clariq-daily-inference-trigger \
  --schedule-expression "cron(0 0 * * ? *)" \
  --state ENABLED \
  --description "Trigger Clariq inference at 12am UTC daily"

echo "✓ EventBridge rule created (12am UTC daily)"
```

### 4.2 Connect Lambda to EventBridge

```bash
# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function-configuration \
  --function-name clariq-daily-inference \
  --query FunctionArn \
  --output text)

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create IAM policy for EventBridge to invoke Lambda
cat > /tmp/event-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "$LAMBDA_ARN",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:events:*:${ACCOUNT_ID}:rule/clariq-daily-inference-trigger"
        }
      }
    }
  ]
}
EOF

# Add permission
aws lambda add-permission \
  --function-name clariq-daily-inference \
  --statement-id clariq-event-permission \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:*:${ACCOUNT_ID}:rule/clariq-daily-inference-trigger"

# Add Lambda as target
aws events put-targets \
  --rule clariq-daily-inference-trigger \
  --targets "Id"="1","Arn"="$LAMBDA_ARN","RoleArn"="arn:aws:iam::${ACCOUNT_ID}:role/clariq-lambda-role"

echo "✓ Lambda connected to EventBridge"
```

### 4.3 Verify Scheduling

```bash
# Check if rule is active
aws events describe-rule \
  --name clariq-daily-inference-trigger

# Check targets
aws events list-targets-by-rule \
  --rule clariq-daily-inference-trigger

echo "✓ Scheduling verified"
```

---

## STEP 5: Upload Data to Production

### 5.1 Prepare Historical Data

```bash
# For each seller, upload historical data
for store_id in store_001 store_002 store_003; do
  # Generate historical data (in production: from Shopify)
  python -c "
from data_pipeline import DataPipeline
p = DataPipeline()
df = p.load_historical_data('$store_id', source='synthetic')
df.to_csv('/tmp/${store_id}_historical.csv', index=False)
"
  
  # Upload to S3
  aws s3 cp /tmp/${store_id}_historical.csv \
    s3://clariq-data-prod/data/${store_id}/
  
  echo "✓ Uploaded ${store_id} historical data"
done
```

### 5.2 Train and Upload Models

```bash
# Train models for each seller
python << 'EOF'
from data_pipeline import DataPipeline
import boto3

pipeline = DataPipeline(aws_bucket='clariq-ml-models-prod')
s3 = boto3.client('s3')

for store_id in ['store_001', 'store_002', 'store_003']:
    # Load data
    df = pipeline.load_historical_data(store_id, source='s3')
    df_prepared = pipeline.prepare_data(df)
    
    # Run inference to get model
    results = pipeline.run_inference(df_prepared)
    
    # Save model
    model_path = pipeline.save_model(store_id, results)
    
    # Upload to S3
    s3.upload_file(
        model_path,
        'clariq-ml-models-prod',
        f'models/{store_id}_model.pkl'
    )
    
    print(f"✓ {store_id}: Model trained and uploaded")
EOF
```

---

## STEP 6: Verification and Testing

### 6.1 Manual Execution Test

```bash
# Manually trigger Lambda to verify everything works
aws lambda invoke \
  --function-name clariq-daily-inference \
  --payload '{"source": "manual-test"}' \
  /tmp/test-response.json

# Check results
python -c "
import json
with open('/tmp/test-response.json') as f:
    result = json.load(f)
    print(json.dumps(result, indent=2))
"
```

### 6.2 Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/clariq-daily-inference --follow
```

### 6.3 Verify Reports Generated

```bash
# Check if reports were generated
aws s3 ls s3://clariq-reports-prod/reports/

# Download and check a report
aws s3 cp \
  s3://clariq-reports-prod/reports/store_001/$(date +%Y-%m-%d)_inference_report.txt \
  /tmp/latest_report.txt

cat /tmp/latest_report.txt
```

---

## STEP 7: Monitoring and Alerts

### 7.1 Set Up CloudWatch Alarms

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name clariq-lambda-errors \
  --alarm-description "Alert if Clariq Lambda fails" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 3600 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=clariq-daily-inference
```

### 7.2 Set Up SNS Notifications

```bash
# Create SNS topic for alerts
aws sns create-topic --name clariq-alerts

# Subscribe to alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:clariq-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

echo "✓ Notifications configured (check email)"
```

---

## STEP 8: Production Checklist

```
DEPLOYMENT CHECKLIST:

Infrastructure:
□ S3 buckets created (data, models, reports)
□ DynamoDB tables created (history, sellers)
□ IAM role created with proper permissions
□ Lambda function deployed

Scheduling:
□ EventBridge rule created (12am UTC)
□ Lambda connected to EventBridge
□ Permission granted for EventBridge → Lambda
□ Scheduling verified

Data:
□ Historical data uploaded to S3
□ Models trained and uploaded
□ Test data in DynamoDB

Testing:
□ Manual Lambda invocation successful
□ Reports generated correctly
□ CloudWatch logs show success
□ S3 contains generated reports

Monitoring:
□ CloudWatch alarms configured
□ SNS notifications enabled
□ Email alerts verified

READY FOR PRODUCTION: ✓
```

---

## RUNNING COSTS

Monthly AWS Costs (Estimated):

```
S3 Storage:        $0.50  (data, models, reports)
Lambda:            $2.00  (30 executions/day)
DynamoDB:          $1.00  (on-demand pricing)
CloudWatch Logs:   $0.30
EventBridge:       $0.10
─────────────────────────
Total/month:       ~$4.00
```

---

## TROUBLESHOOTING

### Lambda Timeout
```bash
# Increase timeout to 15 minutes
aws lambda update-function-configuration \
  --function-name clariq-daily-inference \
  --timeout 900
```

### S3 Access Denied
```bash
# Verify role has S3 permissions
aws iam get-role-policy \
  --role-name clariq-lambda-role \
  --policy-name AmazonS3FullAccess
```

### EventBridge Not Triggering
```bash
# Check rule is enabled
aws events describe-rule \
  --name clariq-daily-inference-trigger

# Check targets
aws events list-targets-by-rule \
  --rule clariq-daily-inference-trigger
```

---

## NEXT STEPS

Once production is running:

1. **Week 1:** Monitor daily runs, fix any issues
2. **Week 2:** Add Shopify integration
3. **Week 3:** Start autonomous execution (price updates, campaigns)
4. **Week 4:** Launch beta users
5. **Week 5:** Track ROI metrics
6. **Week 6:** Full production rollout

---

## SUPPORT

- AWS Lambda docs: https://docs.aws.amazon.com/lambda/
- EventBridge docs: https://docs.aws.amazon.com/eventbridge/
- Local testing: `python local_test_suite.py`
- Manual inference: `python data_pipeline.py`

---

**Status: READY FOR DEPLOYMENT** ✅
