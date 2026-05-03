import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { api } from '../api/client';
import { COLORS, FONTS } from '../theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

function SectionCard({ children, style }) {
  return <View style={[styles.sectionCard, style]}>{children}</View>;
}

function Row({ label, value, valueColor }) {
  return (
    <View style={styles.statRow}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, { color: valueColor || COLORS.text }]}>{value ?? '—'}</Text>
    </View>
  );
}

export default function StatsScreen() {
  const [account, setAccount] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [accRes, pnlRes] = await Promise.all([
        api.account(),
        api.dailyPnl(30),
      ]);
      setAccount(accRes.data);
      setChartData(pnlRes.data);
    } catch (e) {
      setError(e?.message || 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={COLORS.accent} />
      </View>
    );
  }

  // Bar chart: last 14 days with data, skip zeros for label clarity
  let barLabels = [];
  let barValues = [];
  let barColors = [];
  if (chartData?.data?.length) {
    const recent = chartData.data.slice(-14);
    recent.forEach((d, i) => {
      barLabels.push(i % 3 === 0 ? d.date.slice(5) : '');
      barValues.push(Math.abs(d.pnl));
      barColors.push(d.pnl >= 0 ? COLORS.profit : COLORS.loss);
    });
  }

  // Winning days / losing days
  const tradingDays = chartData?.data?.filter((d) => d.trades > 0) ?? [];
  const winDays = tradingDays.filter((d) => d.pnl > 0).length;
  const lossDays = tradingDays.filter((d) => d.pnl <= 0).length;

  const pnlColor = (v) => (v !== null && v >= 0 ? COLORS.profit : COLORS.loss);
  const fmt = (v) =>
    v !== null && v !== undefined ? `${v >= 0 ? '+' : ''}$${Math.abs(v).toFixed(2)}` : '—';

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accent} />}
      contentContainerStyle={styles.content}
    >
      <Text style={styles.title}>Statistics</Text>

      {error && <Text style={styles.errorText}>{error}</Text>}

      {/* Performance summary */}
      <Text style={styles.sectionLabel}>ALL-TIME PERFORMANCE</Text>
      <SectionCard>
        <Row label="Total P&L" value={fmt(account?.all_time_pnl)} valueColor={pnlColor(account?.all_time_pnl)} />
        <Row label="Win Rate" value={`${account?.all_time_win_rate?.toFixed(1) ?? '—'}%`} valueColor={account?.all_time_win_rate >= 50 ? COLORS.profit : COLORS.loss} />
        <Row label="Total Trades" value={account?.total_closed_trades} />
        <Row label="Open Positions" value={account?.open_trades} valueColor={account?.open_trades > 0 ? COLORS.accent : COLORS.text} />
      </SectionCard>

      {/* Today */}
      <Text style={styles.sectionLabel}>TODAY</Text>
      <SectionCard>
        <Row label="P&L" value={fmt(account?.today_pnl)} valueColor={pnlColor(account?.today_pnl)} />
        <Row label="Trades" value={account?.today_trades} />
        <Row label="Wins" value={account?.today_wins} valueColor={COLORS.profit} />
        <Row label="Win Rate" value={`${account?.today_win_rate?.toFixed(1) ?? '—'}%`} valueColor={account?.today_win_rate >= 50 ? COLORS.profit : COLORS.loss} />
      </SectionCard>

      {/* 30-day day summary */}
      <Text style={styles.sectionLabel}>LAST 30 DAYS</Text>
      <SectionCard>
        <Row label="Trading Days" value={tradingDays.length} />
        <Row label="Winning Days" value={winDays} valueColor={COLORS.profit} />
        <Row label="Losing Days" value={lossDays} valueColor={COLORS.loss} />
        <Row
          label="Total P&L"
          value={fmt(chartData?.data?.reduce((s, d) => s + d.pnl, 0) ?? 0)}
          valueColor={pnlColor(chartData?.data?.reduce((s, d) => s + d.pnl, 0) ?? 0)}
        />
      </SectionCard>

      {/* Bar chart */}
      {barValues.length > 0 && (
        <>
          <Text style={styles.sectionLabel}>DAILY P&L (14 DAYS)</Text>
          <View style={styles.chartCard}>
            <BarChart
              data={{
                labels: barLabels,
                datasets: [{ data: barValues.length ? barValues : [0] }],
              }}
              width={SCREEN_WIDTH - 32}
              height={200}
              chartConfig={{
                backgroundColor: COLORS.card,
                backgroundGradientFrom: COLORS.card,
                backgroundGradientTo: COLORS.card,
                decimalPlaces: 2,
                color: (opacity = 1) => `rgba(88, 166, 255, ${opacity})`,
                labelColor: () => COLORS.textMuted,
                propsForBackgroundLines: { stroke: COLORS.border },
                barPercentage: 0.7,
              }}
              style={styles.chart}
              withInnerLines
              showValuesOnTopOfBars={false}
            />
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingBottom: 32 },
  center: { flex: 1, backgroundColor: COLORS.background, justifyContent: 'center', alignItems: 'center' },
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
  sectionCard: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    marginHorizontal: 16,
    paddingHorizontal: 16,
    paddingVertical: 4,
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  statLabel: {
    color: COLORS.textMuted,
    fontFamily: FONTS.mono,
    fontSize: 13,
  },
  statValue: {
    fontFamily: FONTS.mono,
    fontSize: 13,
    fontWeight: '700',
  },
  chartCard: {
    marginHorizontal: 16,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    overflow: 'hidden',
    paddingTop: 8,
  },
  chart: { borderRadius: 12 },
  errorText: {
    color: COLORS.loss,
    textAlign: 'center',
    marginTop: 16,
    fontFamily: FONTS.mono,
    paddingHorizontal: 24,
  },
});
