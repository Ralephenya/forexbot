import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { api } from '../api/client';
import { COLORS, FONTS } from '../theme';

const INSTRUMENTS = [
  'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',
  'GBPJPY', 'USDCAD', 'USDCHF', 'NZDUSD',
];

const LOT_SIZES = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50];

function PriceDisplay({ instrument, loading, price, error }) {
  if (loading) return <ActivityIndicator size="small" color={COLORS.accent} />;
  if (error) return <Text style={styles.priceError}>Price unavailable</Text>;
  if (!price) return null;
  return (
    <View style={styles.priceBox}>
      <View style={styles.priceSide}>
        <Text style={styles.priceLabel}>BID</Text>
        <Text style={[styles.priceValue, { color: COLORS.sell }]}>
          {Number(price.bid).toFixed(5)}
        </Text>
      </View>
      <View style={styles.priceSpread}>
        <Text style={styles.spreadLabel}>{price.spread} pts</Text>
      </View>
      <View style={styles.priceSide}>
        <Text style={styles.priceLabel}>ASK</Text>
        <Text style={[styles.priceValue, { color: COLORS.buy }]}>
          {Number(price.ask).toFixed(5)}
        </Text>
      </View>
    </View>
  );
}

export default function PlaceTradeScreen() {
  const [instrument, setInstrument] = useState('EURUSD');
  const [direction, setDirection] = useState('BUY');
  const [volume, setVolume] = useState(0.01);
  const [useCustomSize, setUseCustomSize] = useState(false);
  const [customSize, setCustomSize] = useState('0.01');
  const [useTP, setUseTP] = useState(false);
  const [useSL, setUseSL] = useState(false);
  const [tpInput, setTpInput] = useState('');
  const [slInput, setSlInput] = useState('');
  const [useStrategy, setUseStrategy] = useState(false);
  const [price, setPrice] = useState(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [priceError, setPriceError] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [account, setAccount] = useState(null);

  const fetchPrice = useCallback(async () => {
    setPriceLoading(true);
    setPriceError(false);
    try {
      const res = await api.livePrice(instrument);
      setPrice(res.data);
    } catch (_) {
      setPriceError(true);
    } finally {
      setPriceLoading(false);
    }
  }, [instrument]);

  const fetchAccount = useCallback(async () => {
    try {
      const res = await api.liveAccount();
      setAccount(res.data);
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchPrice();
    fetchAccount();
    const interval = setInterval(fetchPrice, 5000); // refresh price every 5s
    return () => clearInterval(interval);
  }, [fetchPrice, fetchAccount]);

  const finalVolume = useCustomSize ? parseFloat(customSize) || 0.01 : volume;

  const handlePlace = () => {
    const vol = finalVolume;
    const tp = useTP ? parseFloat(tpInput) : null;
    const sl = useSL ? parseFloat(slInput) : null;

    if (vol < 0.01) {
      Alert.alert('Invalid Size', 'Minimum lot size is 0.01');
      return;
    }
    if (useTP && (!tp || isNaN(tp))) {
      Alert.alert('Invalid TP', 'Enter a valid take profit price');
      return;
    }
    if (useSL && (!sl || isNaN(sl))) {
      Alert.alert('Invalid SL', 'Enter a valid stop loss price');
      return;
    }

    // Validate TP/SL direction
    const currentPrice = direction === 'BUY' ? price?.ask : price?.bid;
    if (tp && currentPrice) {
      const tpValid = direction === 'BUY' ? tp > currentPrice : tp < currentPrice;
      if (useTP && !tpValid) {
        Alert.alert('Invalid TP', `Take profit must be ${direction === 'BUY' ? 'above' : 'below'} current price`);
        return;
      }
    }
    if (sl && currentPrice) {
      const slValid = direction === 'BUY' ? sl < currentPrice : sl > currentPrice;
      if (useSL && !slValid) {
        Alert.alert('Invalid SL', `Stop loss must be ${direction === 'BUY' ? 'below' : 'above'} current price`);
        return;
      }
    }

    const entryPrice = direction === 'BUY' ? price?.ask : price?.bid;

    Alert.alert(
      'Confirm Trade',
      [
        `${direction} ${vol} lots ${instrument}`,
        entryPrice ? `@ ${Number(entryPrice).toFixed(5)}` : '',
        tp ? `TP: ${tp}` : '',
        sl ? `SL: ${sl}` : '',
      ].filter(Boolean).join('\n'),
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: `PLACE ${direction}`,
          style: direction === 'SELL' ? 'destructive' : 'default',
          onPress: async () => {
            setPlacing(true);
            try {
              await api.placeTrade({
                instrument,
                direction,
                volume: vol,
                take_profit: useTP ? tp : undefined,
                stop_loss: useSL ? sl : undefined,
                strategy_name: useStrategy ? 'StrategyB' : 'Manual',
              });
              Alert.alert('Order Placed', `${direction} ${vol} lots ${instrument} opened successfully`);
              // Reset form
              setTpInput('');
              setSlInput('');
              setUseTP(false);
              setUseSL(false);
              fetchAccount();
            } catch (e) {
              const msg = e?.response?.data?.detail || e?.message || 'Order failed';
              Alert.alert('Order Failed', msg);
            } finally {
              setPlacing(false);
            }
          },
        },
      ],
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Place Trade</Text>

      {/* Live account balance */}
      {account && (
        <View style={styles.accountBar}>
          <Text style={styles.accountLabel}>Balance</Text>
          <Text style={styles.accountValue}>${Number(account.balance).toFixed(2)}</Text>
          <Text style={styles.accountLabel}>Equity</Text>
          <Text style={[styles.accountValue, { color: account.equity >= account.balance ? COLORS.profit : COLORS.loss }]}>
            ${Number(account.equity).toFixed(2)}
          </Text>
          <Text style={styles.accountLabel}>Free Margin</Text>
          <Text style={styles.accountValue}>${Number(account.free_margin).toFixed(2)}</Text>
        </View>
      )}

      {/* Instrument selector */}
      <Text style={styles.sectionLabel}>INSTRUMENT</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
        {INSTRUMENTS.map((sym) => (
          <TouchableOpacity
            key={sym}
            style={[styles.chip, instrument === sym && styles.chipActive]}
            onPress={() => setInstrument(sym)}
          >
            <Text style={[styles.chipText, instrument === sym && styles.chipTextActive]}>{sym}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Live price */}
      <PriceDisplay instrument={instrument} loading={priceLoading} price={price} error={priceError} />

      {/* BUY / SELL */}
      <Text style={styles.sectionLabel}>DIRECTION</Text>
      <View style={styles.dirRow}>
        <TouchableOpacity
          style={[styles.dirBtn, styles.buyBtn, direction === 'BUY' && styles.buyBtnActive]}
          onPress={() => setDirection('BUY')}
          activeOpacity={0.8}
        >
          <Text style={[styles.dirBtnText, direction === 'BUY' && styles.dirBtnTextActive]}>
            ▲  BUY
          </Text>
          {price && direction === 'BUY' && (
            <Text style={styles.dirPrice}>{Number(price.ask).toFixed(5)}</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.dirBtn, styles.sellBtn, direction === 'SELL' && styles.sellBtnActive]}
          onPress={() => setDirection('SELL')}
          activeOpacity={0.8}
        >
          <Text style={[styles.dirBtnText, direction === 'SELL' && styles.dirBtnTextActive]}>
            ▼  SELL
          </Text>
          {price && direction === 'SELL' && (
            <Text style={styles.dirPrice}>{Number(price.bid).toFixed(5)}</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Lot size */}
      <Text style={styles.sectionLabel}>LOT SIZE</Text>
      <View style={styles.lotRow}>
        {LOT_SIZES.map((s) => (
          <TouchableOpacity
            key={s}
            style={[styles.lotBtn, !useCustomSize && volume === s && styles.lotBtnActive]}
            onPress={() => { setVolume(s); setUseCustomSize(false); }}
          >
            <Text style={[styles.lotText, !useCustomSize && volume === s && styles.lotTextActive]}>
              {s}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.customRow}>
        <Text style={styles.customLabel}>Custom:</Text>
        <TextInput
          style={[styles.customInput, useCustomSize && styles.customInputActive]}
          value={customSize}
          onChangeText={(v) => { setCustomSize(v); setUseCustomSize(true); }}
          keyboardType="decimal-pad"
          placeholder="0.01"
          placeholderTextColor={COLORS.textMuted}
          onFocus={() => setUseCustomSize(true)}
        />
        <Text style={styles.customLabel}>lots</Text>
      </View>

      {/* TP / SL */}
      <Text style={styles.sectionLabel}>TAKE PROFIT / STOP LOSS</Text>
      <View style={styles.card}>
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>Take Profit</Text>
          <Switch
            value={useTP}
            onValueChange={setUseTP}
            trackColor={{ true: COLORS.profit + '88', false: COLORS.surface }}
            thumbColor={useTP ? COLORS.profit : COLORS.textMuted}
          />
        </View>
        {useTP && (
          <TextInput
            style={styles.priceInput}
            value={tpInput}
            onChangeText={setTpInput}
            placeholder={direction === 'BUY' ? 'e.g. 1.1050' : 'e.g. 1.0800'}
            placeholderTextColor={COLORS.textMuted}
            keyboardType="decimal-pad"
          />
        )}

        <View style={[styles.toggleRow, { marginTop: 12 }]}>
          <Text style={styles.toggleLabel}>Stop Loss</Text>
          <Switch
            value={useSL}
            onValueChange={setUseSL}
            trackColor={{ true: COLORS.loss + '88', false: COLORS.surface }}
            thumbColor={useSL ? COLORS.loss : COLORS.textMuted}
          />
        </View>
        {useSL && (
          <TextInput
            style={styles.priceInput}
            value={slInput}
            onChangeText={setSlInput}
            placeholder={direction === 'BUY' ? 'e.g. 1.0900' : 'e.g. 1.1000'}
            placeholderTextColor={COLORS.textMuted}
            keyboardType="decimal-pad"
          />
        )}
      </View>

      {/* Use strategy defaults */}
      <View style={styles.card}>
        <View style={styles.toggleRow}>
          <View>
            <Text style={styles.toggleLabel}>Use Strategy B TP/SL</Text>
            <Text style={styles.toggleSub}>Auto-calculates based on ATR</Text>
          </View>
          <Switch
            value={useStrategy}
            onValueChange={(v) => {
              setUseStrategy(v);
              if (v) { setUseTP(false); setUseSL(false); }
            }}
            trackColor={{ true: COLORS.accent + '88', false: COLORS.surface }}
            thumbColor={useStrategy ? COLORS.accent : COLORS.textMuted}
          />
        </View>
      </View>

      {/* Place button */}
      <TouchableOpacity
        style={[
          styles.placeBtn,
          direction === 'BUY' ? styles.placeBuy : styles.placeSell,
          (placing || priceLoading) && styles.placeBtnDisabled,
        ]}
        onPress={handlePlace}
        disabled={placing || priceLoading}
        activeOpacity={0.8}
      >
        {placing ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <>
            <Text style={styles.placeBtnText}>
              {direction === 'BUY' ? '▲' : '▼'}  {direction} {finalVolume} lots {instrument}
            </Text>
            {price && (
              <Text style={styles.placeBtnPrice}>
                @ {direction === 'BUY' ? Number(price.ask).toFixed(5) : Number(price.bid).toFixed(5)}
              </Text>
            )}
          </>
        )}
      </TouchableOpacity>

      <Text style={styles.disclaimer}>
        Trades are executed at market price. Always use Stop Loss to protect your account.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingBottom: 40 },
  title: {
    color: COLORS.text, fontSize: 26, fontFamily: FONTS.bold,
    fontWeight: '700', paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8,
  },
  accountBar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: COLORS.card, marginHorizontal: 16, borderRadius: 10,
    padding: 12, marginBottom: 8, flexWrap: 'wrap', gap: 4,
  },
  accountLabel: { color: COLORS.textMuted, fontSize: 10, fontFamily: FONTS.mono, textTransform: 'uppercase' },
  accountValue: { color: COLORS.text, fontSize: 13, fontFamily: FONTS.bold, fontWeight: '700' },
  sectionLabel: {
    color: COLORS.textMuted, fontSize: 11, fontFamily: FONTS.mono,
    textTransform: 'uppercase', letterSpacing: 1, marginHorizontal: 16,
    marginTop: 16, marginBottom: 8,
  },
  chipScroll: { paddingLeft: 16 },
  chip: {
    backgroundColor: COLORS.card, borderRadius: 20, paddingHorizontal: 14,
    paddingVertical: 8, marginRight: 8, borderWidth: 1, borderColor: COLORS.border,
  },
  chipActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  chipText: { color: COLORS.textMuted, fontFamily: FONTS.mono, fontSize: 13, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  priceBox: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: COLORS.card, marginHorizontal: 16, borderRadius: 12,
    padding: 14, marginTop: 8,
  },
  priceSide: { alignItems: 'center', flex: 1 },
  priceLabel: { color: COLORS.textMuted, fontSize: 10, fontFamily: FONTS.mono, textTransform: 'uppercase', marginBottom: 4 },
  priceValue: { fontSize: 18, fontFamily: FONTS.mono, fontWeight: '700' },
  priceSpread: { alignItems: 'center' },
  spreadLabel: { color: COLORS.textMuted, fontSize: 11, fontFamily: FONTS.mono },
  priceError: { color: COLORS.loss, textAlign: 'center', marginTop: 8, fontFamily: FONTS.mono, fontSize: 12 },
  dirRow: { flexDirection: 'row', marginHorizontal: 16, gap: 10 },
  dirBtn: {
    flex: 1, paddingVertical: 18, borderRadius: 12, alignItems: 'center',
    borderWidth: 2, justifyContent: 'center',
  },
  buyBtn: { backgroundColor: COLORS.buy + '15', borderColor: COLORS.buy + '55' },
  buyBtnActive: { backgroundColor: COLORS.buy + '33', borderColor: COLORS.buy },
  sellBtn: { backgroundColor: COLORS.sell + '15', borderColor: COLORS.sell + '55' },
  sellBtnActive: { backgroundColor: COLORS.sell + '33', borderColor: COLORS.sell },
  dirBtnText: { color: COLORS.textMuted, fontSize: 18, fontFamily: FONTS.bold, fontWeight: '700' },
  dirBtnTextActive: { color: COLORS.text },
  dirPrice: { color: COLORS.textMuted, fontSize: 12, fontFamily: FONTS.mono, marginTop: 4 },
  lotRow: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: 16, gap: 8 },
  lotBtn: {
    backgroundColor: COLORS.card, borderRadius: 8, paddingHorizontal: 14,
    paddingVertical: 10, borderWidth: 1, borderColor: COLORS.border,
  },
  lotBtnActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  lotText: { color: COLORS.textMuted, fontFamily: FONTS.mono, fontSize: 14 },
  lotTextActive: { color: '#fff', fontWeight: '700' },
  customRow: {
    flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 10, gap: 8,
  },
  customLabel: { color: COLORS.textMuted, fontFamily: FONTS.mono, fontSize: 13 },
  customInput: {
    backgroundColor: COLORS.card, borderWidth: 1, borderColor: COLORS.border,
    borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8,
    color: COLORS.text, fontFamily: FONTS.mono, fontSize: 14, width: 80,
  },
  customInputActive: { borderColor: COLORS.accent },
  card: {
    backgroundColor: COLORS.card, borderRadius: 12,
    marginHorizontal: 16, padding: 14, marginTop: 4,
  },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  toggleLabel: { color: COLORS.text, fontSize: 14, fontFamily: FONTS.bold },
  toggleSub: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
  priceInput: {
    backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border,
    borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10,
    color: COLORS.text, fontFamily: FONTS.mono, fontSize: 14, marginTop: 8,
  },
  placeBtn: {
    marginHorizontal: 16, marginTop: 20, paddingVertical: 18,
    borderRadius: 14, alignItems: 'center', justifyContent: 'center',
  },
  placeBuy: { backgroundColor: COLORS.buy },
  placeSell: { backgroundColor: COLORS.sell },
  placeBtnDisabled: { opacity: 0.5 },
  placeBtnText: { color: '#fff', fontSize: 18, fontFamily: FONTS.bold, fontWeight: '700' },
  placeBtnPrice: { color: 'rgba(255,255,255,0.8)', fontSize: 13, fontFamily: FONTS.mono, marginTop: 4 },
  disclaimer: {
    color: COLORS.textMuted, fontSize: 11, textAlign: 'center',
    marginHorizontal: 24, marginTop: 16, lineHeight: 16,
  },
});
