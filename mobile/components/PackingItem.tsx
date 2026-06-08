import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

interface PackingItemProps {
  name: string;
  category: string;
  quantity: number;
  weight_grams: number | null;
  is_essential: boolean;
  packed: boolean;
  onToggle: () => void;
}

export default function PackingItemComponent({
  name,
  category,
  quantity,
  weight_grams,
  is_essential,
  packed,
  onToggle,
}: PackingItemProps) {
  const categoryIcons: Record<string, string> = {
    documents: '📄', electronics: '🔌', toiletries: '🧴',
    clothing: '👕', gear: '🎒', other: '📦',
  };

  return (
    <TouchableOpacity
      style={[styles.row, packed && styles.rowPacked]}
      onPress={onToggle}
      activeOpacity={0.6}
    >
      <View style={[styles.checkbox, packed && styles.checkboxChecked]}>
        {packed && <Text style={styles.checkmark}>✓</Text>}
      </View>
      <View style={styles.content}>
        <Text style={[styles.name, packed && styles.namePacked]}>
          {categoryIcons[category] || '📦'} {name}
        </Text>
        <View style={styles.meta}>
          <Text style={styles.qty}>x{quantity}</Text>
          {weight_grams && (
            <Text style={styles.weight}>{(weight_grams / 1000).toFixed(2)} kg</Text>
          )}
          {is_essential && <Text style={styles.essential}>ESSENTIAL</Text>}
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#0f3460',
    backgroundColor: '#1a1a2e',
  },
  rowPacked: { backgroundColor: '#0d1a0d' },
  checkbox: {
    width: 24, height: 24, borderRadius: 12,
    borderWidth: 2, borderColor: '#555',
    marginRight: 12, alignItems: 'center', justifyContent: 'center',
  },
  checkboxChecked: { backgroundColor: '#4ecdc4', borderColor: '#4ecdc4' },
  checkmark: { color: '#1a1a2e', fontWeight: '700', fontSize: 14 },
  content: { flex: 1 },
  name: { color: '#eaeaea', fontSize: 16, fontWeight: '500' },
  namePacked: { color: '#888', textDecorationLine: 'line-through' },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 2, gap: 8 },
  qty: { color: '#aaa', fontSize: 12 },
  weight: { color: '#aaa', fontSize: 12 },
  essential: {
    backgroundColor: '#e94560', color: '#fff',
    fontSize: 9, fontWeight: '700',
    paddingHorizontal: 6, paddingVertical: 1,
    borderRadius: 4, marginLeft: 6,
  },
});