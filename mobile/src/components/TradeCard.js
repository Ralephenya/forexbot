import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { COLORS, FONTS } from '../theme';

function pnlColor(pnl) {
  if (pnl === null || pnl === undefined) return COLORS.textMuted;
  return pnl >= 0 ? COLORS.profit : COLORS.loss;
}

function formatPrice(p) {
  if (p === null || p === undefined) return '—';
  return Number(p).toFixed(5);
}

function formatPnl(pnl) {
  if (pnl === null || pnl === undefined) return '—';
  const sign = pnl >= 0 ? '+' : '';
  return `${sign}$${Number(pnl).toFixed(2)}`;
}

function formatPips(pips) {
  if (pips === null || pips === undefined) return '—';
  const sign = pips >= 0 ? '+' : '';
  return `${sign}${Number(pips).toFixed(1)} pips`;
}

function shortDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) +
    ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

export default function TradeCard({ trade, onPress }) {
  const isOpen = trade.status === 'OPEN';
  const directionColor = trade.direction === 'BUY' ? COLORS.buy : COLORS.sell;

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.75}>
      {/* Header row */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.instrument}>{trade.instrument}</Text>
          <View style={[styles.dirBadge, { backgroundColor: directionColor + '22', borderColor: directionColor }]}>
            <Text style={[styles.dirText, { color: directionColor }]}>{trade.direction}</Text>
          </View>
        </View>
        <View style={styles.headerRight}>
          <View style={[styles.statusBadge, isOpen ? styles.statusOpen : styles.statusClosed]}>
            <Text style={[styles.statusText, isOpen ? styles.statusOpenText : styles.statusClosedText]}>
              {isOpen ? '● OPEN' : 'CLOSED'}
            </Text>
          </View>
        </View>
      </View>

      {/* Prices row */}
      <View style={styles.priceRow}>
        <View>
          <Text style={styles.priceLabel}>Entry</Text>
          <Text style={styles.price}>{formatPrice(trade.entry_price)}</Text>
        </View>
        {trade.take_profit && (
          <View>
            <Text style={styles.priceLabel}>TP</Text>
            <Text style={[styles.price, { color: COLORS.profit }]}>{formatPrice(trade.take_profit)}</Text>
          </View>
        )}
        {trade.stop_loss && (
          <View>
            <Text style={styles.priceLabel}>SL</Text>
            <Text style={[styles.price, { color: COLORS.loss }]}>{formatPrice(trade.stop_loss)}</Text>
          </View>
        )}
        {!isOpen && trade.exit_price && (
          <View>
            <Text style={styles.priceLabel}>Exit</Text>
            <Text style={styles.price}>{formatPrice(trade.exit_price)}</Text>
          </View>
        )}
      </View>

      {/* Footer row */}
      <View style={styles.footer}>
        <Text style={styles.timestamp}>{shortDate(trade.timestamp)}</Text>
        {isOpen ? (
          <Text style={styles.strategy}>{trade.strategy_name || 'Strategy B'}</Text>
        ) : (
          <View style={styles.pnlRow}>
            <Text style={[styles.pnl, { color: pnlColor(trade.pnl) }]}>
              {formatPnl(trade.pnl)}
            </Text>
            <Text style={[styles.pips, { color: pnlColor(trade.pips) }]}>
              {' · '}{formatPips(trade.pips)}
            </Text>
          </View>
        )}
      </View>

      {!isOpen && trade.exit_reason && (
        <Text style={styles.exitReason}>Exit: {trade.exit_reason}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 14,
    marginHorizontal: 16,
    marginVertical: 5,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerRight: {},
  instrument: {
    color: COLORS.text,
    fontSize: 16,
    fontFamily: FONTS.bold,
  },
  dirBadge: {
    borderWidth: 1,
    borderRadius: 5,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  dirText: {
    fontSize: 11,
    fontFamily: FONTS.bold,
  },
  statusBadge: {
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  statusOpen: {
    backgroundColor: COLORS.profit + '22',
  },
  statusClosed: {
    backgroundColor: COLORS.surface,
  },
  statusText: {
    fontSize: 11,
    fontFamily: FONTS.mono,
  },
  statusOpenText: {
    color: COLORS.profit,
  },
  statusClosedText: {
    color: COLORS.textMuted,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  priceLabel: {
    color: COLORS.textMuted,
    fontSize: 10,
    fontFamily: FONTS.mono,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  price: {
    color: COLORS.text,
    fontSize: 13,
    fontFamily: FONTS.mono,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timestamp: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontFamily: FONTS.mono,
  },
  strategy: {
    color: COLORS.accent,
    fontSize: 11,
    fontFamily: FONTS.mono,
  },
  pnlRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pnl: {
    fontSize: 14,
    fontFamily: FONTS.bold,
  },
  pips: {
    fontSize: 12,
    fontFamily: FONTS.mono,
  },
  exitReason: {
    color: COLORS.textMuted,
    fontSize: 10,
    fontFamily: FONTS.mono,
    marginTop: 6,
  },
});
