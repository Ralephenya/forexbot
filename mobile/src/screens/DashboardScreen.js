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
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { api } from '../api/client';
import StatCard from '../components/StatCard';
import { COLORS, FONTS } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function DashboardScreen() {
  const [account, setAccount] = useState(null);
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
      const msg = e?.response?.data?.detail || e?.message || 'Connection failed';
      setError(msg);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // auto-refresh every 30s
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleKillSwitch = () => {
    if (!account) return;
    const newState = account.kill_switch ? 'off' : 'on';
    const action = account.kill_switch ? 'RESUME' : 'STOP';
    Alert.alert(
      `${action} Trading Bot`,
      account.kill_switch
        ? 'This will allow the bot to place new trades. Are you sure?'
        : 'This will stop the bot from placing new trades immediately. Are you sure?',
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
  const fmt = (v, decimals = 2) =>
    v !== undefined && v !== null ? `${v >= 0 ? '+' : ''}$${Math.abs(v).toFixed(decimals)}` : '—';

  // Build chart from last 14 days
  let chartLabels = [];
  let chartValues = [];
  if (chartData?.data?.length) {
    // Show only every 3rd date label to avoid crowding on iPhone SE
    chartData.data.forEach((d, i) => {
      const label = i % 3 === 0 ? d.date.slice(5) : ''; // MM-DD
      chartLabels.push(label);
      chartValues.push(d.pnl);
    });
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accent} />}
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
            {account?.kill_switch ? 'STOPPED' : account?.bot_status || 'LOADING'}
          </Text>
        </View>
      </View>

      {/* Error banner */}
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>Cannot reach API: {error}</Text>
          <Text style={styles.errorHint}>Check Settings → API URL</Text>
        </View>
      )}

      {/* Today's stats */}
      <Text style={styles.sectionLabel}>TODAY</Text>
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

      {/* Open positions */}
      <View style={styles.row}>
        <StatCard
          label="Open Positions"
          value={account?.open_trades ?? '—'}
          valueColor={account?.open_trades > 0 ? COLORS.accent : COLORS.text}
        />
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
      </View>

      {/* P&L Chart — last 14 days */}
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

      {/* Kill switch button */}
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
            ? '▶  RESUME TRADING'
            : '■  STOP TRADING'}
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
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    paddingBottom: 32,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    color: COLORS.text,
    fontSize: 26,
    fontFamily: FONTS.bold,
    fontWeight: '700',
  },
  subtitle: {
    color: COLORS.textMuted,
    fontSize: 13,
    fontFamily: FONTS.mono,
  },
  botStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  botStatusText: {
    color: COLORS.text,
    fontSize: 12,
    fontFamily: FONTS.mono,
    fontWeight: '600',
  },
  errorBanner: {
    marginHorizontal: 16,
    marginVertical: 8,
    backgroundColor: COLORS.loss + '22',
    borderWidth: 1,
    borderColor: COLORS.loss,
    borderRadius: 10,
    padding: 12,
  },
  errorText: {
    color: COLORS.loss,
    fontSize: 13,
    fontFamily: FONTS.mono,
  },
  errorHint: {
    color: COLORS.textMuted,
    fontSize: 11,
    marginTop: 4,
  },
  sectionLabel: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontFamily: FONTS.mono,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 4,
  },
  row: {
    flexDirection: 'row',
    paddingHorizontal: 12,
  },
  chartContainer: {
    marginHorizontal: 16,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    overflow: 'hidden',
    paddingTop: 8,
  },
  chart: {
    borderRadius: 12,
  },
  killBtn: {
    marginHorizontal: 16,
    marginTop: 8,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  killBtnStop: {
    backgroundColor: COLORS.loss + '22',
    borderWidth: 1.5,
    borderColor: COLORS.loss,
  },
  killBtnResume: {
    backgroundColor: COLORS.profit + '22',
    borderWidth: 1.5,
    borderColor: COLORS.profit,
  },
  killBtnText: {
    color: COLORS.text,
    fontSize: 15,
    fontFamily: FONTS.bold,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  updated: {
    color: COLORS.textMuted,
    fontSize: 10,
    fontFamily: FONTS.mono,
    textAlign: 'center',
    marginTop: 16,
  },
});
