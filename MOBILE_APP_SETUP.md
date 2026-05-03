# ForexBot Mobile App — Serverless Setup

Fully serverless. No EC2. No idle costs. Runs 24/7 for free on AWS.

---

## Architecture

```
iPhone SE
    │
    │ (internet — WiFi, 4G, 5G, anywhere)
    │
API Gateway ──► Lambda (FastAPI/Mangum)
                    ├── reads/writes S3  (trade history)
                    └── calls MetaAPI    (live prices, place/close trades)

EventBridge (every 15 min)
    └──► Lambda (Trading Bot)
              ├── fetches candles via MetaAPI
              ├── runs Strategy B (RSI + ATR + EMA)
              ├── places trade via MetaAPI → XM broker
              └── writes result to S3
```

**Cost:** ~$0/month (Lambda + S3 both have generous free tiers)

---

## What the app does

| Tab | Features |
|-----|---------|
| **Dashboard** | Live XM balance, equity, free margin, open positions with real P&L — refreshes every 10s |
| **⚡ Trade** | Place BUY/SELL on 10 pairs — live bid/ask prices every 5s, pick lot size, set TP/SL |
| **History** | All trades — tap any open trade to close it at market |
| **Stats** | 30-day P&L bar chart, win rate, winning/losing days |
| **Settings** | Paste API Gateway URL, test connection |

---

## Prerequisites (one-time installs on your computer)

```bash
# 1. AWS CLI
# Download from https://aws.amazon.com/cli/

# 2. AWS SAM CLI
# Download from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# 3. Docker (needed to build Lambda images)
# Download from https://docs.docker.com/get-docker/

# 4. Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Key, region (e.g. us-east-1)
```

---

## Step 1 — Register MetaAPI (free)

MetaAPI connects your existing XM MT5 account to the cloud.

1. Go to **https://app.metaapi.cloud** → create free account
2. **MT Accounts** → **Add Account** → enter XM credentials:
   - Login (account number)
   - Password
   - Server (e.g. `XMTrading-Demo` or `XMTrading-Real`)
3. Wait ~1 minute for the green dot
4. Copy your **Account ID** (shown on the account card)
5. Go to **API Access** → copy your **API Token**

---

## Step 2 — Deploy to AWS

```bash
cd forexbot
./deploy/deploy_sam.sh
```

The script:
1. Asks for your MetaAPI token, account ID, symbol, lot size
2. Builds a Docker image with all dependencies
3. Pushes it to Amazon ECR
4. Deploys Lambda + API Gateway + S3 + EventBridge via CloudFormation
5. Prints your API URL when done

**Takes about 5-10 minutes the first time.**

Example output:
```
  API URL:   https://abc123xyz.execute-api.us-east-1.amazonaws.com
  S3 Bucket: forexbot-trades-123456789
```

---

## Step 3 — Mobile app

**Install Expo Go** from the App Store on your iPhone SE (free).

On your computer:
```bash
cd forexbot/mobile
npm install
npx expo start
```

Scan the QR code with your iPhone camera → tap the banner → ForexBot opens.

---

## Step 4 — Connect app to AWS

1. Tap **Settings** in the app
2. Paste your API Gateway URL: `https://abc123xyz.execute-api.us-east-1.amazonaws.com`
3. Tap **SAVE** → **TEST CONNECTION**
4. Should show: "Connected! MetaAPI configured: true, storage: s3"

The app now works from anywhere — any WiFi, 4G, 5G. No home network needed.

---

## How the bot works (fully automated)

EventBridge fires the bot Lambda every 15 minutes. Each run:

1. Checks kill switch in S3 — if ON, skips
2. Syncs open positions with MetaAPI (catches TP/SL hits since last run)
3. If no open position: fetches 100 × 15-min candles
4. Calculates RSI(14), ATR(14), EMA(20), volatility regime
5. Strategy B decision:
   - **High volatility** → Mean reversion: BUY if RSI≤30, SELL if RSI≥70
   - **Low volatility** → Breakout: BUY if Close>EMA, SELL if Close<EMA
6. Places trade via MetaAPI → XM broker
7. Records trade in S3

The bot only runs during allowed hours (9, 10, 12, 14 UTC — London session).

---

## Useful commands

```bash
# Watch live bot logs
sam logs -n BotFunction --stack-name forexbot --tail

# Watch API logs
sam logs -n ApiFunction --stack-name forexbot --tail

# Manually trigger the bot (for testing)
aws lambda invoke \
  --function-name $(aws cloudformation describe-stacks \
    --stack-name forexbot \
    --query "Stacks[0].Outputs[?OutputKey=='BotFunctionArn'].OutputValue" \
    --output text) \
  --payload '{"action":"status"}' \
  response.json && cat response.json

# View trade data in S3
aws s3 cp s3://forexbot-trades-YOURACCOUNTID/trades.json - | python -m json.tool

# Remove everything from AWS
sam delete --stack-name forexbot
```

---

## Updating the bot

After changing code:
```bash
./deploy/deploy_sam.sh   # re-runs the full deploy
```
SAM only rebuilds what changed.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "MetaAPI not configured" | Re-run deploy with correct credentials |
| Bot not trading | Check `sam logs -n BotFunction` — might be kill switch or no signal |
| App can't connect | Make sure you pasted the full HTTPS URL (not HTTP) from the deploy output |
| "Trade failed" | Check MetaAPI dashboard — account may have synced out |
| Deploy fails | Make sure Docker is running and `aws configure` is set up |

---

## Cost breakdown

| Service | Free tier | Our usage | Cost |
|---------|-----------|-----------|------|
| Lambda | 1M requests/month, 400K GB-seconds | ~3K requests/month | **$0** |
| API Gateway | 1M requests/month | ~1K requests/month | **$0** |
| S3 | 5GB storage, 20K GET, 2K PUT | <1MB storage, ~100 PUTs | **$0** |
| EventBridge | 14M events/month | ~2K events/month | **$0** |
| ECR (Docker image) | 500MB/month | ~200MB image | **$0** |

**Total: $0/month** (well within free tier forever for this workload)

---

## File structure

```
forexbot/
├── serverless/
│   ├── s3_store.py        ← S3 data layer (replaces SQLite)
│   ├── bot_handler.py     ← Bot Lambda (EventBridge trigger)
│   ├── api_handler.py     ← API Lambda (API Gateway + Mangum)
│   └── requirements.txt
├── trading_system/
│   ├── metaapi_client.py  ← MetaAPI REST client
│   ├── strategy.py        ← Strategy B logic
│   └── indicators.py      ← RSI, ATR, EMA calculations
├── mobile/
│   └── src/screens/       ← 5-tab React Native app
├── template.yaml          ← AWS SAM template
├── Dockerfile.lambda      ← Lambda container image
└── deploy/
    └── deploy_sam.sh      ← One-command deployment
```
