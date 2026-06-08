import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface WeightTrackerProps {
  totalGrams: number;
  limitGrams: number;
}

export default function WeightTracker({ totalGrams, limitGrams }: WeightTrackerProps) {
  const pct = limitGrams > 0 ? Math.round((totalGrams / limitGrams) * 100) : 0;
  const color = pct > 90 ? '#e94560' : pct > 70 ? '#f5a623' : '#4ecdc4';
  const overWeight = totalGrams > limitGrams;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Weight Budget</Text>
        {overWeight && <Text style={styles.overBadge}>OVER LIMIT</Text>}
      </View>
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: Math.min(pct, 100) as any, backgroundColor: color }]} />
      </View>
      <View style={styles.labels}>
        <Text style={styles.weightText}>
          {(totalGrams / 1000).toFixed(1)} / {(limitGrams / 1000).toFixed(1)} kg
        </Text>
        <Text style={[styles.pctText, { color }]}>{pct}%</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#16213e',
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#0f3460',
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  title: { fontSize: 16, fontWeight: 'bold', color: '#e94560' },
  overBadge: { backgroundColor: '#e94560', color: '#fff', fontSize: 10, fontWeight: '700', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  progressBar: { height: 14, backgroundColor: '#0f3460', borderRadius: 7, overflow: 'hidden', marginBottom: 6 },
  progressFill: { height: '100%', borderRadius: 7 },
  labels: { flexDirection: 'row', justifyContent: 'space-between' },
  weightText: { color: '#eaeaea', fontSize: 13 },
  pctText: { fontSize: 13, fontWeight: '700' },
});