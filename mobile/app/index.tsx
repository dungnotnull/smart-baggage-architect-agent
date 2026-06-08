import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import api from '../services/api';

interface QuickStat {
  label: string;
  value: string;
  color: string;
}

export default function HomeScreen() {
  const router = useRouter();
  const [airlineCount, setAirlineCount] = useState(0);
  const [serverOk, setServerOk] = useState(false);

  useEffect(() => {
    (async () => {
      const { data } = await api.healthCheck();
      setServerOk(data?.status === 'ok');
      const { data: airlineData } = await api.listAirlines();
      if (airlineData) {
        setAirlineCount((airlineData as any).count || 0);
      }
    })();
  }, []);

  const stats: QuickStat[] = [
    { label: 'Airlines', value: airlineCount.toString(), color: '#e94560' },
    { label: 'Server', value: serverOk ? 'Online' : 'Offline', color: serverOk ? '#4ecdc4' : '#e94560' },
    { label: 'Model', value: 'YOLOv8n', color: '#f5a623' },
    { label: 'LLM', value: 'Claude', color: '#7c5cfc' },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.appName}>Smart Baggage Architect</Text>
      <Text style={styles.tagline}>Pack smarter. Travel lighter. Never forget a thing.</Text>

      {/* Quick Stats */}
      <View style={styles.statsRow}>
        {stats.map((stat, i) => (
          <View key={i} style={styles.statCard}>
            <Text style={[styles.statValue, { color: stat.color }]}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Main Actions */}
      <TouchableOpacity style={styles.primaryButton} onPress={() => router.push('/trip-setup')}>
        <Text style={styles.primaryButtonText}>+ New Trip</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryButton} onPress={() => router.push('/trip-history')}>
        <Text style={styles.secondaryButtonText}>📋 Trip History</Text>
      </TouchableOpacity>

      {/* Feature Cards */}
      <Text style={styles.sectionTitle}>Features</Text>
      <View style={styles.featureGrid}>
        <View style={styles.featureCard}>
          <Text style={styles.featureIcon}>✈️</Text>
          <Text style={styles.featureName}>50+ Airlines</Text>
          <Text style={styles.featureDesc}>Real baggage policy data</Text>
        </View>
        <View style={styles.featureCard}>
          <Text style={styles.featureIcon}>🌤️</Text>
          <Text style={styles.featureName}>Weather AI</Text>
          <Text style={styles.featureDesc}>7-day forecast + clothing recs</Text>
        </View>
        <View style={styles.featureCard}>
          <Text style={styles.featureIcon}>📷</Text>
          <Text style={styles.featureName}>Camera Scan</Text>
          <Text style={styles.featureDesc}>YOLOv8n on-device detection</Text>
        </View>
        <View style={styles.featureCard}>
          <Text style={styles.featureIcon}>🧠</Text>
          <Text style={styles.featureName}>LLM Advisor</Text>
          <Text style={styles.featureDesc}>Claude + GPT-4o + Phi-3</Text>
        </View>
        <View style={styles.featureCard}>
          <Text style={styles.featureIcon}>⚖️</Text>
          <Text style={styles.featureName}>Weight Optimizer</Text>
          <Text style={styles.featureDesc}>Knapsack + 3D bin-packing</Text>
        </View>
        <View style={styles.featureCard}>
          <Text style={styles.featureIcon}>🔄</Text>
          <Text style={styles.featureName}>Adaptive</Text>
          <Text style={styles.featureDesc}>Learns from your feedback</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  content: { padding: 20, paddingTop: 60 },
  appName: { fontSize: 32, fontWeight: 'bold', color: '#e94560', marginBottom: 4 },
  tagline: { fontSize: 14, color: '#aaa', marginBottom: 24 },
  statsRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  statCard: { flex: 1, backgroundColor: '#16213e', borderRadius: 10, padding: 12, marginHorizontal: 4, alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: '700' },
  statLabel: { fontSize: 11, color: '#888', marginTop: 4 },
  primaryButton: { backgroundColor: '#e94560', borderRadius: 14, padding: 18, alignItems: 'center', marginBottom: 12 },
  primaryButtonText: { color: '#fff', fontSize: 20, fontWeight: '700' },
  secondaryButton: { backgroundColor: '#16213e', borderRadius: 14, padding: 16, alignItems: 'center', marginBottom: 24, borderWidth: 1, borderColor: '#0f3460' },
  secondaryButtonText: { color: '#eaeaea', fontSize: 16, fontWeight: '600' },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#eaeaea', marginBottom: 12 },
  featureGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  featureCard: { width: '48%', backgroundColor: '#16213e', borderRadius: 12, padding: 16, marginBottom: 12, alignItems: 'center', borderWidth: 1, borderColor: '#0f3460' },
  featureIcon: { fontSize: 28, marginBottom: 6 },
  featureName: { color: '#eaeaea', fontSize: 14, fontWeight: '600', textAlign: 'center' },
  featureDesc: { color: '#888', fontSize: 11, textAlign: 'center', marginTop: 2 },
});