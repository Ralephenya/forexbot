import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { api, loadApiUrl, saveApiUrl, getApiUrl } from '../api/client';
import { COLORS, FONTS } from '../theme';

function Row({ label, value, valueColor }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={[styles.infoValue, { color: valueColor || COLORS.text }]}>{value ?? '—'}</Text>
    </View>
  );
}

export default function SettingsScreen() {
  const [url, setUrl] = useState('');
  const [saved, setSaved] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [stratParams, setStratParams] = useState(null);

  useEffect(() => {
    loadApiUrl().then((u) => {
      setUrl(u);
      setSaved(u);
      // Fetch strategy params after URL is loaded
      api.strategyParams().then((r) => setStratParams(r.data)).catch(() => {});
    });
  }, []);

  const handleSave = useCallback(async () => {
    const trimmed = url.trim();
    if (!trimmed) {
      Alert.alert('Invalid URL', 'Please enter a valid URL.');
      return;
    }
    await saveApiUrl(trimmed);
    setSaved(trimmed);
    Alert.alert('Saved', 'API URL has been updated.');
  }, [url]);

  const handleTest = useCallback(async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.health();
      setTestResult({ ok: true, msg: `Connected! DB exists: ${res.data.db_exists}` });
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || 'Connection failed';
      setTestResult({ ok: false, msg });
    } finally {
      setTesting(false);
    }
  }, []);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Settings</Text>

      {/* API URL */}
      <Text style={styles.sectionLabel}>API SERVER</Text>
      <View style={styles.card}>
        <Text style={styles.helpText}>
          After deploying with SAM, paste your API Gateway URL here.
          {'\n\n'}It looks like:{'\n'}
          <Text style={styles.code}>https://xxxxxx.execute-api.us-east-1.amazonaws.com</Text>
          {'\n\n'}Find it in the terminal output after{' '}
          <Text style={styles.code}>./deploy/deploy_sam.sh</Text>
          {', '}or in the AWS Console → CloudFormation → forexbot → Outputs → ApiUrl.
          {'\n\n'}For local testing (same WiFi):{'\n'}
          <Text style={styles.code}>http://192.168.1.x:8000</Text>
        </Text>
        <TextInput
          style={styles.input}
          value={url}
          onChangeText={setUrl}
          placeholder="https://xxxxxx.execute-api.us-east-1.amazonaws.com"
          placeholderTextColor={COLORS.textMuted}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
        <View style={styles.btnRow}>
          <TouchableOpacity
            style={[styles.btn, styles.btnPrimary]}
            onPress={handleSave}
            activeOpacity={0.75}
          >
            <Text style={styles.btnText}>SAVE</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.btnSecondary]}
            onPress={handleTest}
            activeOpacity={0.75}
            disabled={testing}
          >
            {testing ? (
              <ActivityIndicator size="small" color={COLORS.text} />
            ) : (
              <Text style={styles.btnText}>TEST CONNECTION</Text>
            )}
          </TouchableOpacity>
        </View>
        {testResult && (
          <View style={[styles.testResult, testResult.ok ? styles.testOk : styles.testFail]}>
            <Text style={[styles.testText, { color: testResult.ok ? COLORS.profit : COLORS.loss }]}>
              {testResult.ok ? '✓ ' : '✗ '}{testResult.msg}
            </Text>
          </View>
        )}
      </View>

      {/* Current config */}
      <Text style={styles.sectionLabel}>CURRENT CONFIG</Text>
      <View style={styles.card}>
        <Row label="API URL" value={saved} valueColor={COLORS.accent} />
      </View>

      {/* How to deploy */}
      <Text style={styles.sectionLabel}>HOW TO DEPLOY (ONE TIME)</Text>
      <View style={styles.card}>
        <Text style={styles.helpText}>
          Prerequisites: AWS CLI, SAM CLI, Docker installed on your computer.
        </Text>
        <View style={styles.codeBlock}>
          <Text style={styles.codeBlockText}>
            {'cd forexbot\n./deploy/deploy_sam.sh'}
          </Text>
        </View>
        <Text style={styles.helpText}>
          The script asks for your MetaAPI credentials and deploys everything to AWS automatically.
          {'\n\n'}After ~5 minutes it prints your API URL — paste it above.
          {'\n\n'}Cost: effectively $0 (Lambda free tier = 1M requests/month,
          S3 free tier = 5GB storage). The bot runs 24/7 for free.
        </Text>
      </View>

      {/* Strategy params (live from API) */}
      {stratParams && (
        <>
          <Text style={styles.sectionLabel}>CONFLUENCE STRATEGY (OPTIMIZED)</Text>
          <View style={styles.card}>
            <Row
              label="Min Confluence Score"
              value={`${stratParams.confluence.min_score} / ${stratParams.confluence.max_score}`}
              valueColor={COLORS.accent}
            />
            <Row
              label="RSI Buy / Sell"
              value={`≤${stratParams.rsi.buy_threshold} / ≥${stratParams.rsi.sell_threshold}`}
            />
            <Row
              label="Target / Stop (ATR×)"
              value={`${stratParams.risk.target_atr_mult}× / ${stratParams.risk.stop_atr_mult}×`}
            />
            <Row label="Session (UTC)" value={`${stratParams.session.start_utc}:00 – ${stratParams.session.end_utc}:00`} />
          </View>

          <Text style={styles.sectionLabel}>BACKTEST RESULTS (12 MONTHS)</Text>
          <View style={styles.card}>
            <Row
              label="Win Rate"
              value={`${stratParams.backtest.win_rate_pct}%`}
              valueColor={COLORS.profit}
            />
            <Row
              label="Profit Factor"
              value={`${stratParams.backtest.profit_factor}×`}
              valueColor={COLORS.profit}
            />
            <Row
              label="Sharpe Ratio"
              value={String(stratParams.backtest.sharpe_ratio)}
              valueColor={COLORS.profit}
            />
            <Row
              label="Avg Pips / Month"
              value={`+${stratParams.backtest.avg_pips_per_month}`}
              valueColor={COLORS.profit}
            />
            <Row
              label="Max Drawdown"
              value={`${stratParams.backtest.max_drawdown_pips} pips`}
              valueColor={COLORS.loss}
            />
            <Row label="Total Trades" value={String(stratParams.backtest.total_trades)} />
            <Row label="Method" value={stratParams.backtest.method} />
          </View>
        </>
      )}

      {/* App info */}
      <Text style={styles.sectionLabel}>ABOUT</Text>
      <View style={styles.card}>
        <Row label="App Version" value="2.0.0" />
        <Row label="Strategy" value="Strategy B + Confluence Engine" valueColor={COLORS.accent} />
        <Row label="Pairs" value="EUR/USD · GBP/USD · USD/JPY" />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingBottom: 48 },
  title: {
    color: COLORS.text,
    fontSize: 26,
    fontFamily: FONTS.bold,
    fontWeight: '700',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  sectionLabel: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontFamily: FONTS.mono,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 8,
  },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    marginHorizontal: 16,
    padding: 16,
    gap: 12,
  },
  helpText: {
    color: COLORS.textMuted,
    fontSize: 13,
    lineHeight: 20,
  },
  code: {
    color: COLORS.accent,
    fontFamily: FONTS.mono,
    fontSize: 12,
  },
  input: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: COLORS.text,
    fontFamily: FONTS.mono,
    fontSize: 14,
  },
  btnRow: {
    flexDirection: 'row',
    gap: 8,
  },
  btn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnPrimary: {
    backgroundColor: COLORS.accent,
  },
  btnSecondary: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  btnText: {
    color: COLORS.text,
    fontFamily: FONTS.bold,
    fontWeight: '700',
    fontSize: 13,
    letterSpacing: 0.5,
  },
  testResult: {
    borderRadius: 8,
    padding: 10,
  },
  testOk: { backgroundColor: COLORS.profit + '18' },
  testFail: { backgroundColor: COLORS.loss + '18' },
  testText: { fontFamily: FONTS.mono, fontSize: 13 },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  infoLabel: { color: COLORS.textMuted, fontFamily: FONTS.mono, fontSize: 12 },
  infoValue: { fontFamily: FONTS.mono, fontSize: 12, fontWeight: '600', flex: 1, textAlign: 'right', paddingLeft: 8 },
  codeBlock: {
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  codeBlockText: {
    color: COLORS.accent,
    fontFamily: FONTS.mono,
    fontSize: 12,
    lineHeight: 20,
  },
});
