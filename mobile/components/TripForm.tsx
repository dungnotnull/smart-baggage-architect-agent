import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface TripFormProps {
  airline: string;
  destination: string;
  origin: string;
  departureDate: string;
  returnDate: string;
  cabinClass: string;
  activityType: string;
}

export default function TripForm({
  airline,
  destination,
  origin,
  departureDate,
  returnDate,
  cabinClass,
  activityType,
}: TripFormProps) {
  return (
    <View style={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{airline}</Text>
      </View>
      <Text style={styles.route}>
        {origin} → {destination}
      </Text>
      <Text style={styles.dates}>
        {departureDate} — {returnDate}
      </Text>
      <View style={styles.tags}>
        <Text style={styles.tag}>{cabinClass}</Text>
        <Text style={styles.tag}>{activityType}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#16213e',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#0f3460',
  },
  badge: {
    backgroundColor: '#e94560',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  badgeText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  route: { color: '#eaeaea', fontSize: 20, fontWeight: '700', marginBottom: 4 },
  dates: { color: '#aaa', fontSize: 13, marginBottom: 8 },
  tags: { flexDirection: 'row', gap: 8 },
  tag: {
    backgroundColor: '#0f3460',
    color: '#eaeaea',
    fontSize: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    overflow: 'hidden',
  },
});