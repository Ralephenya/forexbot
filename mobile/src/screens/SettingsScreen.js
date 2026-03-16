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

  useEffect(() => {
    loadApiUrl().then((u) => {
      setUrl(u);
      setSaved(u);
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
          Enter the IP address of the computer running the ForexBot API.
          {'\n'}Make sure both devices are on the same WiFi network.
          {'\n\n'}Find your computer's IP:
          {'\n'}• Windows: run <Text style={styles.code}>ipconfig</Text>
          {'\n'}• Mac/Linux: run <Text style={styles.code}>ifconfig</Text>
        </Text>
        <TextInput
          style={styles.input}
          value={url}
          onChangeText={setUrl}
          placeholder="http://192.168.1.100:8000"
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

      {/* How to run the API */}
      <Text style={styles.sectionLabel}>HOW TO START THE API</Text>
      <View style={styles.card}>
        <Text style={styles.helpText}>
          On your computer, open a terminal in the forexbot folder and run:
        </Text>
        <View style={styles.codeBlock}>
          <Text style={styles.codeBlockText}>
            {'cd forexbot\npip install -r api/requirements.txt\npython -m uvicorn api.main:app --host 0.0.0.0 --port 8000'}
          </Text>
        </View>
        <Text style={styles.helpText}>
          Keep this terminal open while using the app.
          {'\n'}The API will auto-restart when the trading bot updates the database.
        </Text>
      </View>

      {/* App info */}
      <Text style={styles.sectionLabel}>ABOUT</Text>
      <View style={styles.card}>
        <Row label="App Version" value="1.0.0" />
        <Row label="Strategy" value="Strategy B (Regime Switching)" valueColor={COLORS.accent} />
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
