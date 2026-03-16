# ForexBot Mobile App — Full Cloud Setup

No PC needed. Everything runs on AWS EC2 24/7.
Your iPhone SE connects directly to the cloud server.

---

## Architecture

```
iPhone SE
    │
    │  (internet — any connection: WiFi, 4G, 5G)
    │
AWS EC2 (Linux t2.micro — always on)
    ├── FastAPI backend  (port 8000)
    └── Trading bot      (runs strategy every 15 min)
            │
        MetaAPI Cloud
            │
        XM Broker (your MT5 account)
```

---

## What the app can do

| Tab | What you can do |
|-----|----------------|
| **Dashboard** | Live account balance, equity, free margin, open positions with live P&L |
| **Trade ⚡** | Place BUY/SELL trades on 10 pairs, set TP/SL, pick lot size |
| **History** | All trades, tap any open trade → **Close at market** |
| **Stats** | 30-day performance, bar charts |
| **Settings** | Enter EC2 IP, test connection |

---

## Step 1 — Register MetaAPI (free)

MetaAPI connects your existing XM account to the cloud without installing MT5.

1. Go to **https://app.metaapi.cloud** and create a free account
2. Click **"MT Accounts"** → **"Add Account"**
3. Enter your XM credentials:
   - Login (account number)
   - Password
   - Server (e.g. `XMTrading-Demo` or `XMTrading-Real`)
4. Wait ~1 minute for it to connect — you'll see a green dot
5. Copy your **Account ID** (shown on the account card)
6. Go to **"API Access"** → copy your **API Token**

Keep both values — you'll need them in Step 3.

---

## Step 2 — Launch an AWS EC2 instance

1. Log into your AWS console → **EC2** → **Launch Instance**
2. Settings:
   - **Name**: forexbot
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: t2.micro (free tier eligible)
   - **Key pair**: Create or use existing (you'll need the .pem file)
   - **Security group**: Allow inbound **SSH (22)** and **Custom TCP 8000**
3. Launch the instance
4. Note the **Public IPv4 address** (e.g. `54.123.45.67`)

---

## Step 3 — Deploy ForexBot on EC2

SSH into your EC2 instance:
```bash
ssh -i your-key.pem ubuntu@54.123.45.67
```

Run the setup script (copy these commands one by one):
```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# 2. Copy your forexbot folder to EC2 (run this on YOUR computer, not EC2):
#    scp -i your-key.pem -r ./forexbot ubuntu@54.123.45.67:~/

# 3. Back on EC2 — enter the forexbot folder
cd ~/forexbot

# 4. Create your .env file
cp .env.example .env
nano .env
```

In the nano editor, fill in:
```
METAAPI_TOKEN=paste_your_token_here
METAAPI_ACCOUNT_ID=paste_your_account_id_here
DEMO_MODE=true
```
Save: `Ctrl+X` → `Y` → `Enter`

```bash
# 5. Start everything
docker compose up -d --build

# 6. Check it's working
docker compose logs -f
```

You should see `Application startup complete` in the logs.

Test the API in your browser: `http://54.123.45.67:8000/health`
You should see: `{"status":"ok","metaapi_configured":true}`

---

## Step 4 — Install the mobile app on your iPhone SE

**Install Expo Go** from the App Store (free).

On your computer, in the `forexbot/mobile` folder:
```bash
npm install
npx expo start
```

Scan the QR code with your iPhone camera → tap the banner → ForexBot opens.

---

## Step 5 — Connect the app to your EC2

1. Tap **Settings** (bottom right)
2. Enter: `http://54.123.45.67:8000`  ← your EC2 public IP
3. Tap **SAVE** → **TEST CONNECTION**
4. You should see "Connected! MetaAPI configured: true"

You're live. The app works on any internet connection now — WiFi, 4G, 5G.

---

## Placing a trade

1. Tap the **⚡ Trade** tab
2. Select instrument (EURUSD, GBPUSD, etc.)
3. Tap **BUY** or **SELL**
4. Pick your lot size (0.01 = micro lot = ~$0.10/pip)
5. Optionally set Take Profit / Stop Loss
6. Tap the big **BUY / SELL** button
7. Confirm → trade is live

---

## Closing a trade

1. Tap **History** tab
2. Filter by **OPEN**
3. Tap the trade card
4. Scroll down → tap **Close Position at Market**
5. Confirm

---

## Stopping the bot

On **Dashboard** → tap **■ STOP BOT**
This sets a kill switch flag in the database. The bot stops placing new trades.
Tap **▶ RESUME BOT** to re-enable.

---

## Keeping EC2 costs low

| Instance | Cost | Suitable for |
|----------|------|-------------|
| t2.micro | Free (first 12 months) | Perfect for running the bot |
| t3.micro | ~$8/month after free tier | Same performance |

The API + bot together use less than 200MB RAM, well within t2.micro limits.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cannot reach API" | Check the EC2 IP in Settings, make sure port 8000 is open in AWS Security Group |
| "MetaAPI not configured" | Check your .env file on EC2 has the right token and account ID |
| Trade fails | Check MetaAPI dashboard — account may need to resync |
| Bot not trading | Check `docker compose logs bot` on EC2 |
| Port 8000 blocked | EC2 → Security Groups → add Inbound rule: Custom TCP 8000 0.0.0.0/0 |

---

## File structure

```
forexbot/
├── api/
│   ├── main.py              ← FastAPI (trade placement, live prices, history)
│   └── requirements.txt
├── trading_system/
│   ├── metaapi_client.py    ← MetaAPI client (replaces MT5Client)
│   ├── main.py              ← Trading bot (updated to use MetaAPI)
│   └── ...
├── mobile/
│   ├── App.js               ← 5-tab navigation
│   └── src/
│       ├── screens/
│       │   ├── DashboardScreen.js   ← Live balance + positions
│       │   ├── PlaceTradeScreen.js  ← Place BUY/SELL trades
│       │   ├── TradesScreen.js      ← History + close trades
│       │   ├── StatsScreen.js       ← Charts
│       │   └── SettingsScreen.js    ← API URL config
│       └── api/client.js    ← All API calls
├── Dockerfile
├── docker-compose.yml
├── .env.example             ← Copy to .env, fill in credentials
└── deploy/
    └── setup_ec2.sh         ← EC2 bootstrap script
```
