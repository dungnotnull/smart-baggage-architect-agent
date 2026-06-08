import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
  DimensionValue,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import api from '../services/api';

interface PackingItemData {
  id: string;
  name: string;
  category: string;
  quantity: number;
  weight_grams: number | null;
  is_essential: boolean;
  packed: boolean;
  notes: string | null;
}

interface PackingListResponse {
  trip_id: string;
  packing_list: {
    items: PackingItemData[];
    total_weight_grams: number;
    weight_limit_grams: number;
    weight_utilization_pct: number;
  };
  llm_advice: string | null;
  missing_items_alert: string[];
}

export default function PackingListScreen() {
  const { tripId } = useLocalSearchParams<{ tripId: string }>();
  const router = useRouter();
  const [items, setItems] = useState<PackingItemData[]>([]);
  const [totalWeight, setTotalWeight] = useState(0);
  const [weightLimit, setWeightLimit] = useState(23000);
  const [llmAdvice, setLlmAdvice] = useState<string | null>(null);
  const [missingAlert, setMissingAlert] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const loadList = useCallback(async () => {
    if (!tripId) return;
    setLoading(true);
    const { data, error } = await api.getPackingList(tripId);
    if (error) {
      Alert.alert('Error', error);
      setLoading(false);
      return;
    }
    if (data) {
      const resp = data as unknown as PackingListResponse;
      const pl = resp.packing_list || (data as Record<string, unknown>);
      const plItems = (pl as Record<string, unknown>).items as PackingItemData[] || [];
      setItems(plItems);
      setTotalWeight(Number((pl as Record<string, unknown>).total_weight_grams) || 0);
      setWeightLimit(Number((pl as Record<string, unknown>).weight_limit_grams) || 23000);
      setLlmAdvice(resp.llm_advice || null);
      setMissingAlert(resp.missing_items_alert || []);
    }
    setLoading(false);
  }, [tripId]);

  useEffect(() => { loadList(); }, [loadList]);

  const togglePacked = async (item: PackingItemData) => {
    const newPacked = !item.packed;
    setItems(prev => prev.map(i => i.id === item.id ? { ...i, packed: newPacked } : i));
    await api.updatePackingItem(tripId!, item.id, { packed: newPacked });
  };

  const handleOptimize = async () => {
    const { data, error } = await api.optimizePacking(tripId!);
    if (error) { Alert.alert('Error', error); return; }
    if (data) { Alert.alert('Optimization', 'Load order suggestions generated. Check your packing list.'); }
  };

  const handleRegenerate = async () => {
    const { data, error } = await api.regeneratePackingList(tripId!);
    if (error) { Alert.alert('Error', error); return; }
    loadList();
  };

  const pct = weightLimit > 0 ? Math.round((totalWeight / weightLimit) * 100) : 0;
  const barColor = pct > 90 ? '#e94560' : pct > 70 ? '#f5a623' : '#4ecdc4';

  const categories = ['documents', 'electronics', 'toiletries', 'clothing', 'gear', 'other'];
  const categoryIcons: Record<string, string> = {
    documents: '\u{1F4C4}', electronics: '\u{1F50C}', toiletries: '\u{1F9F4}',
    clothing: '\u{1F455}', gear: '\u{1F392}', other: '\u{1F4E6}',
  };

  const renderItem = ({ item }: { item: PackingItemData }) => (
    <TouchableOpacity
      style={[styles.itemRow, item.packed && styles.itemRowPacked]}
      onPress={() => togglePacked(item)}
      activeOpacity={0.6}
    >
      <View style={[styles.checkbox, item.packed && styles.checkboxChecked]}>
        {item.packed && <Text style={styles.checkmark}>&#10003;</Text>}
      </View>
      <View style={styles.itemContent}>
        <Text style={[styles.itemName, item.packed && styles.itemNamePacked]}>
          {categoryIcons[item.category] || '\u{1F4E6}'} {item.name}
        </Text>
        <View style={styles.itemMeta}>
          <Text style={styles.itemQty}>x{item.quantity}</Text>
          {item.weight_grams && (
            <Text style={styles.itemWeight}>{(item.weight_grams / 1000).toFixed(2)} kg</Text>
          )}
          {item.is_essential && <Text style={styles.essentialBadge}>ESSENTIAL</Text>}
        </View>
        {item.notes ? <Text style={styles.itemNotes}>{item.notes}</Text> : null}
      </View>
    </TouchableOpacity>
  );

  const sortedItems = [...items].sort((a, b) => {
    const catDiff = categories.indexOf(a.category) - categories.indexOf(b.category);
    if (catDiff !== 0) return catDiff;
    if (a.is_essential !== b.is_essential) return a.is_essential ? -1 : 1;
    return 0;
  });

  return (
    <View style={styles.container}>
      {/* Weight Tracker */}
      <View style={styles.weightSection}>
        <Text style={styles.weightTitle}>Weight Budget</Text>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: Math.min(pct, 100) as DimensionValue, backgroundColor: barColor }]} />
        </View>
        <Text style={styles.weightLabel}>
          {(totalWeight / 1000).toFixed(1)} / {(weightLimit / 1000).toFixed(1)} kg ({pct}%)
        </Text>
      </View>

      {/* Missing Items Alert */}
      {missingAlert.length > 0 && (
        <View style={styles.alertSection}>
          <Text style={styles.alertTitle}>&#9888;&#65039; Missing Essentials</Text>
          {missingAlert.map((name, i) => (
            <Text key={i} style={styles.alertItem}>&#8226; {name}</Text>
          ))}
        </View>
      )}

      {/* LLM Advice */}
      {llmAdvice && (
        <View style={styles.adviceSection}>
          <Text style={styles.adviceTitle}>&#128161; AI Advice</Text>
          <Text style={styles.adviceText}>{llmAdvice}</Text>
        </View>
      )}

      {/* Action buttons */}
      <View style={styles.actionRow}>
        <TouchableOpacity style={styles.actionBtn} onPress={handleOptimize}>
          <Text style={styles.actionBtnText}>&#9889; Optimize</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={handleRegenerate}>
          <Text style={styles.actionBtnText}>&#128260; Regenerate</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => router.push({ pathname: '/camera-scan', params: { tripId } })}>
          <Text style={styles.actionBtnText}>&#128247; Scan</Text>
        </TouchableOpacity>
      </View>

      {/* Item List */}
      <FlatList
        data={sortedItems}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={loadList} tintColor="#e94560" />}
        contentContainerStyle={styles.listContent}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  weightSection: { padding: 16, backgroundColor: '#16213e', borderBottomWidth: 1, borderBottomColor: '#0f3460' },
  weightTitle: { fontSize: 16, fontWeight: 'bold', color: '#e94560', marginBottom: 8 },
  progressBar: { height: 14, backgroundColor: '#0f3460', borderRadius: 7, overflow: 'hidden', marginBottom: 6 },
  progressFill: { height: '100%', borderRadius: 7 },
  weightLabel: { color: '#eaeaea', fontSize: 13 },
  alertSection: { padding: 12, backgroundColor: '#3d0f0f', borderBottomWidth: 1, borderBottomColor: '#5a1a1a' },
  alertTitle: { color: '#e94560', fontWeight: '700', fontSize: 14, marginBottom: 4 },
  alertItem: { color: '#ff9999', fontSize: 13, marginLeft: 8 },
  adviceSection: { padding: 12, backgroundColor: '#0f3460', borderBottomWidth: 1, borderBottomColor: '#16213e' },
  adviceTitle: { color: '#f5a623', fontWeight: '700', fontSize: 14, marginBottom: 4 },
  adviceText: { color: '#ccc', fontSize: 13, lineHeight: 18 },
  actionRow: { flexDirection: 'row', justifyContent: 'space-around', padding: 12, backgroundColor: '#16213e' },
  actionBtn: { backgroundColor: '#0f3460', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, borderWidth: 1, borderColor: '#e94560' },
  actionBtnText: { color: '#e94560', fontSize: 14, fontWeight: '600' },
  listContent: { paddingBottom: 40 },
  itemRow: { flexDirection: 'row', alignItems: 'center', padding: 14, borderBottomWidth: 1, borderBottomColor: '#0f3460', backgroundColor: '#1a1a2e' },
  itemRowPacked: { backgroundColor: '#0d1a0d' },
  checkbox: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: '#555', marginRight: 12, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: '#4ecdc4', borderColor: '#4ecdc4' },
  checkmark: { color: '#1a1a2e', fontWeight: '700', fontSize: 14 },
  itemContent: { flex: 1 },
  itemName: { color: '#eaeaea', fontSize: 16, fontWeight: '500' },
  itemNamePacked: { color: '#888', textDecorationLine: 'line-through' },
  itemMeta: { flexDirection: 'row', alignItems: 'center', marginTop: 2, gap: 8 },
  itemQty: { color: '#aaa', fontSize: 12 },
  itemWeight: { color: '#aaa', fontSize: 12 },
  essentialBadge: { backgroundColor: '#e94560', color: '#fff', fontSize: 9, fontWeight: '700', paddingHorizontal: 6, paddingVertical: 1, borderRadius: 4, marginLeft: 6 },
  itemNotes: { color: '#888', fontSize: 11, marginTop: 2 },
});