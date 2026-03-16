#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ForexBot — AWS SAM Deployment Script
# Deploys Lambda + EventBridge + S3 + API Gateway
#
# Prerequisites:
#   1. AWS CLI installed and configured (aws configure)
#   2. AWS SAM CLI installed: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
#   3. Docker running (needed to build Lambda container images)
#   4. MetaAPI credentials ready
#
# Usage:
#   chmod +x deploy/deploy_sam.sh
#   ./deploy/deploy_sam.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

STACK_NAME="forexbot"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ForexBot Serverless Deployment"
echo "════════════════════════════════════════════════════════"
echo ""

# ── Check prerequisites ───────────────────────────────────────────────────────
for cmd in aws sam docker; do
    if ! command -v $cmd &>/dev/null; then
        echo "ERROR: '$cmd' is not installed."
        case $cmd in
            aws)   echo "  Install: https://aws.amazon.com/cli/" ;;
            sam)   echo "  Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" ;;
            docker) echo "  Install: https://docs.docker.com/get-docker/" ;;
        esac
        exit 1
    fi
done

if ! docker info &>/dev/null; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Prerequisites OK"
echo ""

# ── Prompt for MetaAPI credentials ──────────────────────────────────────────
echo "Enter your MetaAPI credentials."
echo "(Get them from https://app.metaapi.cloud)"
echo ""

read -p "MetaAPI Token: " META_TOKEN
if [ -z "$META_TOKEN" ]; then
    echo "ERROR: MetaAPI token is required"
    exit 1
fi

read -p "MetaAPI Account ID: " META_ACCOUNT_ID
if [ -z "$META_ACCOUNT_ID" ]; then
    echo "ERROR: MetaAPI account ID is required"
    exit 1
fi

read -p "Trading symbol [EURUSD]: " SYMBOL
SYMBOL="${SYMBOL:-EURUSD}"

read -p "Position size in lots [0.01]: " LOT_SIZE
LOT_SIZE="${LOT_SIZE:-0.01}"

read -p "Demo mode? (true/false) [true]: " DEMO
DEMO="${DEMO:-true}"

echo ""
echo "Summary:"
echo "  Stack:          $STACK_NAME"
echo "  Region:         $REGION"
echo "  Symbol:         $SYMBOL"
echo "  Lot size:       $LOT_SIZE"
echo "  Demo mode:      $DEMO"
echo ""
read -p "Deploy? (y/N): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Cancelled."
    exit 0
fi

# ── Build (compiles the Docker image) ────────────────────────────────────────
echo ""
echo "[1/3] Building Lambda container image..."
sam build \
    --use-container \
    --region "$REGION"

echo "✓ Build complete"

# ── Deploy ────────────────────────────────────────────────────────────────────
echo ""
echo "[2/3] Deploying to AWS..."
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --resolve-image-repos \
    --parameter-overrides \
        MetaApiToken="$META_TOKEN" \
        MetaApiAccountId="$META_ACCOUNT_ID" \
        TradingSymbol="$SYMBOL" \
        PositionSize="$LOT_SIZE" \
        DemoMode="$DEMO"

echo "✓ Deployment complete"

# ── Print API URL ──────────────────────────────────────────────────────────────
echo ""
echo "[3/3] Getting API URL..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='TradeBucketName'].OutputValue" \
    --output text)

echo ""
echo "════════════════════════════════════════════════════════"
echo "  DEPLOYMENT SUCCESSFUL"
echo "════════════════════════════════════════════════════════"
echo ""
echo "  API URL:    $API_URL"
echo "  S3 Bucket:  $BUCKET"
echo ""
echo "  ➜ Open the ForexBot mobile app"
echo "  ➜ Go to Settings"
echo "  ➜ Paste the API URL above"
echo "  ➜ Tap 'Test Connection'"
echo ""
echo "  Useful commands:"
echo "    View bot logs:  sam logs -n BotFunction --stack-name $STACK_NAME --tail"
echo "    View API logs:  sam logs -n ApiFunction --stack-name $STACK_NAME --tail"
echo "    Teardown:       sam delete --stack-name $STACK_NAME"
echo ""
