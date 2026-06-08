import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import api from '../services/api';

interface TripItem {
  trip_id: string;
  destination: string;
  departure_date: string;
  return_date: string;
  airline_iata: string;
  cabin_class: string;
  item_count: number;
  packed_count: number;
  total_weight_grams: number;
  weight_limit_grams: number;
}

export default function TripHistoryScreen() {
  const router = useRouter();
  const [trips, setTrips] = useState<TripItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTrips = useCallback(async () => {
    setLoading(true);
    const { data, error } = await api.listTrips();
    if (data && Array.isArray(data)) {
      setTrips(data as unknown as TripItem[]);
    }
    if (error) {
      Alert.alert('Error', error);
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadTrips(); }, [loadTrips]);

  const formatDate = (d: string) => {
    try { return new Date(d).toLocaleDateString(); } catch { return d; }
  };

  const weightKg = (grams: number) => (grams / 1000).toFixed(1);

  const deleteTrip = async (tripId: string) => {
    Alert.alert('Delete Trip?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await api.deleteTrip(tripId);
          loadTrips();
        },
      },
    ]);
  };

  const renderItem = ({ item }: { item: TripItem }) => {
    const pct = item.weight_limit_grams > 0
      ? Math.round((item.total_weight_grams / item.weight_limit_grams) * 100)
      : 0;
    const barColor = pct > 90 ? '#e94560' : pct > 70 ? '#f5a623' : '#4ecdc4';

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push({ pathname: '/packing-list', params: { tripId: item.trip_id } })}
        onLongPress={() => deleteTrip(item.trip_id)}
        activeOpacity={0.7}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardDestination}>{item.destination}</Text>
          <Text style={styles.cardAirline}>{item.airline_iata}</Text>
        </View>
        <Text style={styles.cardDates}>
          {formatDate(item.departure_date)} - {formatDate(item.return_date)}
        </Text>
        <View style={styles.cardFooter}>
          <Text style={styles.cardWeight}>
            {weightKg(item.total_weight_grams)} / {weightKg(item.weight_limit_grams)} kg
          </Text>
          <Text style={styles.cardProgress}>
            {item.packed_count}/{item.item_count} packed
          </Text>
        </View>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: Math.min(pct, 100) as any, backgroundColor: barColor }]} />
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Trip History</Text>
      <FlatList
        data={trips}
        keyExtractor={(item) => item.trip_id}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={loadTrips} tintColor="#e94560" />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No trips yet. Create one!</Text>
            <TouchableOpacity style={styles.emptyButton} onPress={() => router.push('/trip-setup')}>
              <Text style={styles.emptyButtonText}>New Trip</Text>
            </TouchableOpacity>
          </View>
        }
        contentContainerStyle={trips.length === 0 ? styles.emptyList : undefined}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#e94560', padding: 16 },
  card: {
    backgroundColor: '#16213e',
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#0f3460',
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  cardDestination: { fontSize: 20, fontWeight: '700', color: '#eaeaea' },
  cardAirline: { fontSize: 14, fontWeight: '600', color: '#e94560', backgroundColor: '#1a1a2e', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  cardDates: { fontSize: 13, color: '#aaa', marginBottom: 8 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  cardWeight: { fontSize: 13, color: '#eaeaea' },
  cardProgress: { fontSize: 13, color: '#4ecdc4' },
  progressBar: { height: 4, backgroundColor: '#0f3460', borderRadius: 2, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 2 },
  empty: { alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  emptyList: { flex: 1 },
  emptyText: { color: '#888', fontSize: 16, marginBottom: 16 },
  emptyButton: { backgroundColor: '#e94560', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 10 },
  emptyButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});