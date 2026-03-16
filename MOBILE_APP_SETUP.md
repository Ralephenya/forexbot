# ForexBot Mobile App — Setup Guide

A dark-theme React Native app for your iPhone SE that shows live trades,
P&L charts, and lets you stop the bot with one tap.

---

## What you get

| Screen | What it shows |
|--------|--------------|
| **Dashboard** | Today's P&L, win rate, open positions, 14-day chart, Kill Switch button |
| **Trades** | Full trade history — filter by ALL / OPEN / CLOSED, tap any trade for details |
| **Stats** | 30-day performance, winning/losing days, bar chart |
| **Settings** | Enter your computer's IP address, test connection |

---

## Step 1 — Start the API on your computer

The API reads your existing SQLite trade database and serves it to your phone.

```bash
# From the forexbot folder:
pip install -r api/requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Keep this terminal open while using the app.
The API will automatically pick up new trades as the bot runs.

**Find your computer's local IP address:**
- Windows: open Command Prompt → `ipconfig` → look for IPv4 Address
- Mac: open Terminal → `ifconfig | grep "inet "` → look for 192.168.x.x
- Linux: `hostname -I`

---

## Step 2 — Install Expo Go on your iPhone SE

1. Open the **App Store** on your iPhone SE
2. Search for **"Expo Go"**
3. Install it (free)

---

## Step 3 — Run the mobile app

On your computer (a separate terminal from the API):

```bash
cd mobile
npm install
npx expo start
```

A QR code will appear in the terminal.

1. Open the **Camera** app on your iPhone SE
2. Point it at the QR code
3. Tap the banner that appears → **Expo Go** opens the app

Both your computer and iPhone must be on the **same WiFi network**.

---

## Step 4 — Enter your API URL in the app

1. In the app, tap **Settings** (bottom right)
2. Enter your computer's IP: `http://192.168.1.xxx:8000`
3. Tap **SAVE** then **TEST CONNECTION**
4. You should see "Connected!"

---

## Stop/Resume the bot from your phone

On the **Dashboard** screen, tap the **STOP TRADING** button.
This writes a kill switch flag to the database that the trading bot checks.
Tap **RESUME TRADING** to re-enable it.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cannot reach API" | Check the IP in Settings, make sure both devices are on the same WiFi |
| API won't start | Run `pip install -r api/requirements.txt` first |
| No trades showing | The trading bot hasn't run yet — the DB is empty but the app works fine |
| QR code won't scan | Make sure Expo Go is installed, try scanning with the Camera app |
| App won't open on phone | Tap the Expo Go notification banner that appears after scanning |

---

## Auto-refresh

The Dashboard refreshes every **30 seconds** automatically.
Pull down on any screen to refresh immediately.

---

## Directory structure

```
forexbot/
├── api/
│   ├── main.py          ← FastAPI backend (run this on your computer)
│   └── requirements.txt
├── mobile/
│   ├── App.js           ← Root navigation
│   ├── src/
│   │   ├── api/client.js        ← API calls
│   │   ├── screens/
│   │   │   ├── DashboardScreen.js
│   │   │   ├── TradesScreen.js
│   │   │   ├── StatsScreen.js
│   │   │   └── SettingsScreen.js
│   │   ├── components/
│   │   │   ├── TradeCard.js
│   │   │   └── StatCard.js
│   │   └── theme.js             ← Colors and fonts
│   ├── package.json
│   └── app.json
└── MOBILE_APP_SETUP.md  ← This file
```
