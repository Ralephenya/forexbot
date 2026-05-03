import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Modal,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../api/client';
import TradeCard from '../components/TradeCard';
import { COLORS, FONTS } from '../theme';

const FILTERS = ['ALL', 'OPEN', 'CLOSED'];

function DetailRow({ label, value, valueColor }) {
  return (
    <View style={detailStyles.row}>
      <Text style={detailStyles.label}>{label}</Text>
      <Text style={[detailStyles.value, { color: valueColor || COLORS.text }]}>{value ?? '—'}</Text>
    </View>
  );
}

const detailStyles = StyleSheet.create({
  row: {
    flexDirection: 'row', justifyContent: 'space-between',
    paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  label: { color: COLORS.textMuted, fontFamily: FONTS.mono, fontSize: 13 },
  value: { fontFamily: FONTS.mono, fontSize: 13, fontWeight: '600' },
});

export default function TradesScreen() {
  const [trades, setTrades] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState(null);
  const [closing, setClosing] = useState(false);

  const fetchTrades = useCallback(async () => {
    try {
      setError(null);
      const params = {};
      if (filter !== 'ALL') params.status = filter;
      params.limit = 100;
      const res = await api.trades(params);
      setTrades(res.data);
    } catch (e) {
      setError(e?.message || 'Failed to load trades');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchTrades();
    setRefreshing(false);
  }, [fetchTrades]);

  useEffect(() => {
    setLoading(true);
    fetchTrades();
  }, [fetchTrades]);

  const handleClosePosition = (trade) => {
    if (!trade.broker_ticket) {
      Alert.alert(
        'Cannot Close',
        'This trade has no broker ticket — it may have been placed before MetaAPI was configured.',
      );
      return;
    }
    Alert.alert(
      'Close Position',
      `Close ${trade.direction} ${trade.instrument}?\nThis will close at the current market price.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'CLOSE NOW',
          style: 'destructive',
          onPress: async () => {
            setClosing(true);
            try {
              await api.closeTrade(trade.broker_ticket);
              setSelected(null);
              await fetchTrades();
              Alert.alert('Closed', `${trade.direction} ${trade.instrument} position closed.`);
            } catch (e) {
              const msg = e?.response?.data?.detail || e?.message || 'Close failed';
              Alert.alert('Error', msg);
            } finally {
              setClosing(false);
            }
          },
        },
      ],
    );
  };

  const pnlColor = (v) => {
    if (v === null || v === undefined) return COLORS.textMuted;
    return v >= 0 ? COLORS.profit : COLORS.loss;
  };
  const formatPrice = (p) => (p !== null && p !== undefined ? Number(p).toFixed(5) : '—');
  const formatPnl = (pnl) => {
    if (pnl === null || pnl === undefined) return '—';
    return `${pnl >= 0 ? '+' : ''}$${Number(pnl).toFixed(2)}`;
  };

  return (
    <View style={styles.container}>
      {/* Filter tabs */}
      <View style={styles.filterRow}>
        {FILTERS.map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterBtn, filter === f && styles.filterBtnActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator style={{ marginTop: 40 }} color={COLORS.accent} />
      ) : error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : (
        <FlatList
          data={trades}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <TradeCard trade={item} onPress={() => setSelected(item)} />
          )}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accent} />}
          contentContainerStyle={styles.list}
          ListEmptyComponent={<Text style={styles.empty}>No trades found</Text>}
        />
      )}

      {/* Trade detail modal */}
      <Modal
        visible={!!selected}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelected(null)}
      >
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {selected?.instrument} · {selected?.direction}
            </Text>
            <TouchableOpacity onPress={() => setSelected(null)}>
              <Text style={styles.modalClose}>✕</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalBody}>
            <DetailRow
              label="Status"
              value={selected?.status}
              valueColor={selected?.status === 'OPEN' ? COLORS.profit : COLORS.textMuted}
            />
            <DetailRow
              label="Direction"
              value={selected?.direction}
              valueColor={selected?.direction === 'BUY' ? COLORS.buy : COLORS.sell}
            />
            <DetailRow label="Entry Price" value={formatPrice(selected?.entry_price)} />
            <DetailRow label="Exit Price" value={formatPrice(selected?.exit_price)} />
            <DetailRow label="Take Profit" value={formatPrice(selected?.take_profit)} valueColor={COLORS.profit} />
            <DetailRow label="Stop Loss" value={formatPrice(selected?.stop_loss)} valueColor={COLORS.loss} />
            <DetailRow label="Units" value={selected?.units} />
            <DetailRow
              label="P&L"
              value={formatPnl(selected?.pnl)}
              valueColor={pnlColor(selected?.pnl)}
            />
            <DetailRow
              label="Pips"
              value={selected?.pips !== null ? `${Number(selected?.pips || 0).toFixed(1)} pips` : '—'}
              valueColor={pnlColor(selected?.pips)}
            />
            <DetailRow label="Exit Reason" value={selected?.exit_reason} />
            <DetailRow
              label="Strategy"
              value={selected?.strategy_name || 'Strategy B'}
              valueColor={COLORS.accent}
            />
            <DetailRow
              label="Opened"
              value={selected?.timestamp ? new Date(selected.timestamp).toLocaleString() : '—'}
            />
            <DetailRow label="Broker Ticket" value={selected?.broker_ticket || 'N/A'} valueColor={COLORS.textMuted} />
            <DetailRow label="Trade ID" value={`#${selected?.id}`} valueColor={COLORS.textMuted} />

            {/* Close position button — only for open trades */}
            {selected?.status === 'OPEN' && (
              <TouchableOpacity
                style={styles.closeBtn}
                onPress={() => handleClosePosition(selected)}
                disabled={closing}
                activeOpacity={0.8}
              >
                {closing ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.closeBtnText}>⬛  Close Position at Market</Text>
                )}
              </TouchableOpacity>
            )}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  filterRow: {
    flexDirection: 'row', marginHorizontal: 16, marginVertical: 12,
    backgroundColor: COLORS.card, borderRadius: 10, padding: 4,
  },
  filterBtn: { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center' },
  filterBtnActive: { backgroundColor: COLORS.accent },
  filterText: { color: COLORS.textMuted, fontSize: 13, fontFamily: FONTS.bold, fontWeight: '600' },
  filterTextActive: { color: '#fff' },
  list: { paddingBottom: 24 },
  empty: {
    color: COLORS.textMuted, textAlign: 'center',
    marginTop: 60, fontSize: 15, fontFamily: FONTS.mono,
  },
  errorText: {
    color: COLORS.loss, textAlign: 'center', marginTop: 40,
    fontFamily: FONTS.mono, paddingHorizontal: 24,
  },
  modal: { flex: 1, backgroundColor: COLORS.background },
  modalHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingTop: 20, paddingBottom: 16,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  modalTitle: { color: COLORS.text, fontSize: 20, fontFamily: FONTS.bold, fontWeight: '700' },
  modalClose: { color: COLORS.textMuted, fontSize: 20, padding: 4 },
  modalBody: { paddingHorizontal: 20, paddingTop: 8 },
  closeBtn: {
    backgroundColor: COLORS.loss, borderRadius: 12, paddingVertical: 16,
    alignItems: 'center', marginTop: 24, marginBottom: 12,
  },
  closeBtnText: { color: '#fff', fontSize: 16, fontFamily: FONTS.bold, fontWeight: '700' },
});
