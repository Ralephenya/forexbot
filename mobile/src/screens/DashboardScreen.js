import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { api } from '../api/client';
import StatCard from '../components/StatCard';
import { COLORS, FONTS } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function DashboardScreen({ navigation }) {
  const [account, setAccount] = useState(null);
  const [liveAccount, setLiveAccount] = useState(null);
  const [livePositions, setLivePositions] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [killSwitchLoading, setKillSwitchLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [accRes, pnlRes] = await Promise.all([
        api.account(),
        api.dailyPnl(14),
      ]);
      setAccount(accRes.data);
      setChartData(pnlRes.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Connection failed');
    }
  }, []);

  const fetchLive = useCallback(async () => {
    try {
      const [liveRes, posRes] = await Promise.all([
        api.liveAccount(),
        api.livePositions(),
      ]);
      setLiveAccount(liveRes.data);
      setLivePositions(Array.isArray(posRes.data) ? posRes.data : []);
    } catch (_) {
      // Live data optional — don't show error if MetaAPI not yet configured
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchData(), fetchLive()]);
    setRefreshing(false);
  }, [fetchData, fetchLive]);

  useEffect(() => {
    fetchData();
    fetchLive();
    const histInterval = setInterval(fetchData, 30000);
    const liveInterval = setInterval(fetchLive, 10000); // live data every 10s
    return () => {
      clearInterval(histInterval);
      clearInterval(liveInterval);
    };
  }, [fetchData, fetchLive]);

  const handleKillSwitch = () => {
    if (!account) return;
    const newState = account.kill_switch ? 'off' : 'on';
    const action = account.kill_switch ? 'RESUME' : 'STOP';
    Alert.alert(
      `${action} Trading Bot`,
      account.kill_switch
        ? 'Allow the bot to place new trades?'
        : 'Stop the bot from placing new trades immediately?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: action,
          style: account.kill_switch ? 'default' : 'destructive',
          onPress: async () => {
            setKillSwitchLoading(true);
            try {
              await api.killSwitch(newState);
              await fetchData();
            } catch (e) {
              Alert.alert('Error', 'Failed to update kill switch');
            } finally {
              setKillSwitchLoading(false);
            }
          },
        },
      ],
    );
  };

  const pnlColor = (v) => (v >= 0 ? COLORS.profit : COLORS.loss);
  const fmt = (v, d = 2) =>
    v !== undefined && v !== null
      ? `${v >= 0 ? '+' : ''}$${Math.abs(v).toFixed(d)}`
      : '—';

  // Chart
  let chartLabels = [];
  let chartValues = [];
  if (chartData?.data?.length) {
    chartData.data.forEach((d, i) => {
      chartLabels.push(i % 3 === 0 ? d.date.slice(5) : '');
      chartValues.push(d.pnl);
    });
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accent} />
      }
      contentContainerStyle={styles.content}
    >
      {/* Header */}
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.title}>ForexBot</Text>
          <Text style={styles.subtitle}>Dashboard</Text>
        </View>
        <View style={styles.botStatusRow}>
          <View style={[styles.statusDot, { backgroundColor: account?.kill_switch ? COLORS.loss : COLORS.profit }]} />
          <Text style={styles.botStatusText}>
            {account?.kill_switch ? 'STOPPED' : 'RUNNING'}
          </Text>
        </View>
      </View>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>Cannot reach API: {error}</Text>
          <Text style={styles.errorHint}>Check Settings → API URL</Text>
        </View>
      )}

      {/* Live broker balance (from MetaAPI) */}
      {liveAccount && (
        <>
          <Text style={styles.sectionLabel}>LIVE ACCOUNT (XM)</Text>
          <View style={styles.liveCard}>
            <View style={styles.liveRow}>
              <View style={styles.liveStat}>
                <Text style={styles.liveLabel}>Balance</Text>
                <Text style={styles.liveValue}>${Number(liveAccount.balance).toFixed(2)}</Text>
              </View>
              <View style={styles.liveStat}>
                <Text style={styles.liveLabel}>Equity</Text>
                <Text style={[styles.liveValue, { color: liveAccount.equity >= liveAccount.balance ? COLORS.profit : COLORS.loss }]}>
                  ${Number(liveAccount.equity).toFixed(2)}
                </Text>
              </View>
              <View style={styles.liveStat}>
                <Text style={styles.liveLabel}>Free Margin</Text>
                <Text style={styles.liveValue}>${Number(liveAccount.free_margin).toFixed(2)}</Text>
              </View>
            </View>
            <View style={styles.liveRow}>
              <View style={styles.liveStat}>
                <Text style={styles.liveLabel}>Open Positions</Text>
                <Text style={[styles.liveValue, { color: liveAccount.open_positions > 0 ? COLORS.accent : COLORS.text }]}>
                  {liveAccount.open_positions}
                </Text>
              </View>
              <View style={styles.liveStat}>
                <Text style={styles.liveLabel}>Leverage</Text>
                <Text style={styles.liveValue}>1:{liveAccount.leverage}</Text>
              </View>
              <View style={styles.liveStat}>
                <Text style={styles.liveLabel}>Currency</Text>
                <Text style={styles.liveValue}>{liveAccount.currency}</Text>
              </View>
            </View>
          </View>
        </>
      )}

      {/* Open positions from broker */}
      {livePositions.length > 0 && (
        <>
          <Text style={styles.sectionLabel}>OPEN POSITIONS ({livePositions.length})</Text>
          {livePositions.map((pos) => (
            <View key={String(pos.ticket)} style={styles.posCard}>
              <View style={styles.posHeader}>
                <Text style={styles.posSymbol}>{pos.symbol}</Text>
                <View style={[
                  styles.posDirBadge,
                  { backgroundColor: (pos.direction === 'BUY' ? COLORS.buy : COLORS.sell) + '22' }
                ]}>
                  <Text style={[styles.posDirText, { color: pos.direction === 'BUY' ? COLORS.buy : COLORS.sell }]}>
                    {pos.direction}
                  </Text>
                </View>
                <Text style={[styles.posProfit, { color: (pos.profit || 0) >= 0 ? COLORS.profit : COLORS.loss }]}>
                  {(pos.profit || 0) >= 0 ? '+' : ''}${Number(pos.profit || 0).toFixed(2)}
                </Text>
              </View>
              <View style={styles.posDetails}>
                <Text style={styles.posDetail}>{pos.volume} lots</Text>
                <Text style={styles.posDetail}>Open: {Number(pos.entry_price).toFixed(5)}</Text>
                <Text style={styles.posDetail}>Now: {Number(pos.current_price).toFixed(5)}</Text>
              </View>
            </View>
          ))}
        </>
      )}

      {/* Today's stats */}
      <Text style={styles.sectionLabel}>TODAY (BOT HISTORY)</Text>
      <View style={styles.row}>
        <StatCard
          label="P&L"
          value={account ? fmt(account.today_pnl) : '—'}
          valueColor={account ? pnlColor(account.today_pnl) : COLORS.textMuted}
        />
        <StatCard
          label="Trades"
          value={account?.today_trades ?? '—'}
          sub={account ? `${account.today_wins} wins` : ''}
        />
        <StatCard
          label="Win Rate"
          value={account ? `${account.today_win_rate}%` : '—'}
          valueColor={account ? (account.today_win_rate >= 50 ? COLORS.profit : COLORS.loss) : COLORS.textMuted}
        />
      </View>
      <View style={styles.row}>
        <StatCard
          label="All-Time P&L"
          value={account ? fmt(account.all_time_pnl) : '—'}
          valueColor={account ? pnlColor(account.all_time_pnl) : COLORS.textMuted}
          small
        />
        <StatCard
          label="All Win Rate"
          value={account ? `${account.all_time_win_rate}%` : '—'}
          valueColor={account ? (account.all_time_win_rate >= 50 ? COLORS.profit : COLORS.loss) : COLORS.textMuted}
        />
        <StatCard
          label="Total Trades"
          value={account?.total_closed_trades ?? '—'}
        />
      </View>

      {/* Chart */}
      {chartValues.length > 0 && (
        <>
          <Text style={styles.sectionLabel}>14-DAY P&L</Text>
          <View style={styles.chartContainer}>
            <LineChart
              data={{
                labels: chartLabels,
                datasets: [{ data: chartValues.length ? chartValues : [0] }],
              }}
              width={SCREEN_WIDTH - 32}
              height={180}
              chartConfig={{
                backgroundColor: COLORS.card,
                backgroundGradientFrom: COLORS.card,
                backgroundGradientTo: COLORS.card,
                decimalPlaces: 2,
                color: (opacity = 1) => `rgba(88, 166, 255, ${opacity})`,
                labelColor: () => COLORS.textMuted,
                propsForDots: { r: '3', strokeWidth: '2', stroke: COLORS.accent },
                propsForBackgroundLines: { stroke: COLORS.border },
              }}
              bezier
              style={styles.chart}
              withInnerLines
              withOuterLines={false}
            />
          </View>
        </>
      )}

      {/* Quick Trade button */}
      <TouchableOpacity
        style={styles.quickTradeBtn}
        onPress={() => navigation.navigate('Trade')}
        activeOpacity={0.8}
      >
        <Text style={styles.quickTradeBtnText}>⚡  Place Trade Now</Text>
      </TouchableOpacity>

      {/* Kill switch */}
      <Text style={styles.sectionLabel}>BOT CONTROL</Text>
      <TouchableOpacity
        style={[
          styles.killBtn,
          account?.kill_switch ? styles.killBtnResume : styles.killBtnStop,
        ]}
        onPress={handleKillSwitch}
        disabled={killSwitchLoading || !account}
        activeOpacity={0.75}
      >
        <Text style={styles.killBtnText}>
          {killSwitchLoading
            ? 'UPDATING...'
            : account?.kill_switch
            ? '▶  RESUME BOT'
            : '■  STOP BOT'}
        </Text>
      </TouchableOpacity>

      {account?.last_updated && (
        <Text style={styles.updated}>
          Updated {new Date(account.last_updated).toLocaleTimeString()}
        </Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingBottom: 32 },
  headerRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'flex-start', paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8,
  },
  title: { color: COLORS.text, fontSize: 26, fontFamily: FONTS.bold, fontWeight: '700' },
  subtitle: { color: COLORS.textMuted, fontSize: 13, fontFamily: FONTS.mono },
  botStatusRow: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.card,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20, gap: 6,
  },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  botStatusText: { color: COLORS.text, fontSize: 12, fontFamily: FONTS.mono, fontWeight: '600' },
  errorBanner: {
    marginHorizontal: 16, marginVertical: 8, backgroundColor: COLORS.loss + '22',
    borderWidth: 1, borderColor: COLORS.loss, borderRadius: 10, padding: 12,
  },
  errorText: { color: COLORS.loss, fontSize: 13, fontFamily: FONTS.mono },
  errorHint: { color: COLORS.textMuted, fontSize: 11, marginTop: 4 },
  sectionLabel: {
    color: COLORS.textMuted, fontSize: 11, fontFamily: FONTS.mono,
    textTransform: 'uppercase', letterSpacing: 1, marginHorizontal: 16,
    marginTop: 16, marginBottom: 4,
  },
  liveCard: {
    backgroundColor: COLORS.card, borderRadius: 12, marginHorizontal: 16,
    padding: 14, borderWidth: 1, borderColor: COLORS.accent + '44',
  },
  liveRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  liveStat: { flex: 1, alignItems: 'center' },
  liveLabel: { color: COLORS.textMuted, fontSize: 10, fontFamily: FONTS.mono, textTransform: 'uppercase', marginBottom: 2 },
  liveValue: { color: COLORS.text, fontSize: 14, fontFamily: FONTS.bold, fontWeight: '700' },
  posCard: {
    backgroundColor: COLORS.card, borderRadius: 12, marginHorizontal: 16,
    marginBottom: 8, padding: 12,
  },
  posHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  posSymbol: { color: COLORS.text, fontSize: 15, fontFamily: FONTS.bold, fontWeight: '700' },
  posDirBadge: { borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2 },
  posDirText: { fontSize: 11, fontFamily: FONTS.bold, fontWeight: '700' },
  posProfit: { marginLeft: 'auto', fontSize: 15, fontFamily: FONTS.bold, fontWeight: '700' },
  posDetails: { flexDirection: 'row', gap: 12 },
  posDetail: { color: COLORS.textMuted, fontSize: 11, fontFamily: FONTS.mono },
  row: { flexDirection: 'row', paddingHorizontal: 12 },
  chartContainer: {
    marginHorizontal: 16, backgroundColor: COLORS.card,
    borderRadius: 12, overflow: 'hidden', paddingTop: 8,
  },
  chart: { borderRadius: 12 },
  quickTradeBtn: {
    marginHorizontal: 16, marginTop: 16, paddingVertical: 14,
    borderRadius: 12, alignItems: 'center', backgroundColor: COLORS.accent,
  },
  quickTradeBtnText: { color: '#fff', fontSize: 16, fontFamily: FONTS.bold, fontWeight: '700' },
  killBtn: {
    marginHorizontal: 16, marginTop: 8, paddingVertical: 14,
    borderRadius: 12, alignItems: 'center', justifyContent: 'center',
  },
  killBtnStop: { backgroundColor: COLORS.loss + '22', borderWidth: 1.5, borderColor: COLORS.loss },
  killBtnResume: { backgroundColor: COLORS.profit + '22', borderWidth: 1.5, borderColor: COLORS.profit },
  killBtnText: { color: COLORS.text, fontSize: 15, fontFamily: FONTS.bold, fontWeight: '700', letterSpacing: 0.5 },
  updated: { color: COLORS.textMuted, fontSize: 10, fontFamily: FONTS.mono, textAlign: 'center', marginTop: 16 },
});
