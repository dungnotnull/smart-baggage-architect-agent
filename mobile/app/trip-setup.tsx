import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import api from '../services/api';

const AIRLINE_CODES = [
  'AA','UA','DL','WN','AS','B6','NK','F9','AC','WS',
  'BA','LH','AF','KL','FR','U2','LX','OS','SK','AZ',
  'EK','QR','EY','TK','SV',
  'SQ','NH','JL','CX','KE','OZ','CA','MU','CZ','CI',
  'QF','NZ','GA','TG','MH','PR','AI','6E',
  'LA','AV','G3','ET','SA','MS','KQ',
];

const CABIN_CLASSES = ['economy', 'business', 'first'];
const ACTIVITY_TYPES = ['leisure', 'business', 'adventure', 'family'];

export default function TripSetupScreen() {
  const router = useRouter();
  const [airline, setAirline] = useState('AA');
  const [flightNumber, setFlightNumber] = useState('');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('2026-07-01');
  const [returnDate, setReturnDate] = useState('2026-07-08');
  const [passengers, setPassengers] = useState('1');
  const [cabinClass, setCabinClass] = useState('economy');
  const [activityType, setActivityType] = useState('leisure');
  const [loading, setLoading] = useState(false);

  const handleCreateTrip = useCallback(async () => {
    if (!destination.trim()) {
      Alert.alert('Missing Info', 'Please enter a destination city.');
      return;
    }
    if (!departureDate || !returnDate) {
      Alert.alert('Missing Info', 'Please enter travel dates.');
      return;
    }

    setLoading(true);
    try {
      const { data, error } = await api.createTrip({
        airline_iata: airline,
        flight_number: flightNumber || null,
        origin: origin || 'Home',
        destination: destination.trim(),
        departure_date: departureDate,
        return_date: returnDate,
        passenger_count: parseInt(passengers, 10) || 1,
        cabin_class: cabinClass,
        activity_type: activityType,
      });

      if (error) {
        Alert.alert('Error', error);
        return;
      }

      if ((data as any)?.trip?.trip_id) {
        router.push({
          pathname: '/packing-list',
          params: { tripId: (data as any).trip.trip_id },
        });
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to create trip. Check your connection.');
    } finally {
      setLoading(false);
    }
  }, [airline, flightNumber, origin, destination, departureDate, returnDate, passengers, cabinClass, activityType]);

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>New Trip</Text>

      <Text style={styles.label}>Airline</Text>
      <ScrollView horizontal style={styles.chipRow} showsHorizontalScrollIndicator={false}>
        {AIRLINE_CODES.map((code) => (
          <TouchableOpacity
            key={code}
            style={[styles.chip, airline === code && styles.chipActive]}
            onPress={() => setAirline(code)}
          >
            <Text style={[styles.chipText, airline === code && styles.chipTextActive]}>
              {code}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Text style={styles.label}>Flight Number (optional)</Text>
      <TextInput style={styles.input} value={flightNumber} onChangeText={setFlightNumber} placeholder="e.g. AA123" autoCapitalize="characters" />

      <Text style={styles.label}>Origin</Text>
      <TextInput style={styles.input} value={origin} onChangeText={setOrigin} placeholder="e.g. New York" />

      <Text style={styles.label}>Destination *</Text>
      <TextInput style={styles.input} value={destination} onChangeText={setDestination} placeholder="e.g. Tokyo" />

      <Text style={styles.label}>Departure Date</Text>
      <TextInput style={styles.input} value={departureDate} onChangeText={setDepartureDate} placeholder="YYYY-MM-DD" />

      <Text style={styles.label}>Return Date</Text>
      <TextInput style={styles.input} value={returnDate} onChangeText={setReturnDate} placeholder="YYYY-MM-DD" />

      <Text style={styles.label}>Passengers</Text>
      <TextInput style={styles.input} value={passengers} onChangeText={setPassengers} placeholder="1" keyboardType="numeric" />

      <Text style={styles.label}>Cabin Class</Text>
      <ScrollView horizontal style={styles.chipRow} showsHorizontalScrollIndicator={false}>
        {CABIN_CLASSES.map((cls) => (
          <TouchableOpacity
            key={cls}
            style={[styles.chip, cabinClass === cls && styles.chipActive]}
            onPress={() => setCabinClass(cls)}
          >
            <Text style={[styles.chipText, cabinClass === cls && styles.chipTextActive]}>
              {cls}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Text style={styles.label}>Activity Type</Text>
      <ScrollView horizontal style={styles.chipRow} showsHorizontalScrollIndicator={false}>
        {ACTIVITY_TYPES.map((type) => (
          <TouchableOpacity
            key={type}
            style={[styles.chip, activityType === type && styles.chipActive]}
            onPress={() => setActivityType(type)}
          >
            <Text style={[styles.chipText, activityType === type && styles.chipTextActive]}>
              {type}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleCreateTrip}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Creating Trip...' : 'Generate Packing List'}
        </Text>
      </TouchableOpacity>

      <View style={styles.spacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e', padding: 16 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#e94560', marginBottom: 20 },
  label: { fontSize: 14, color: '#eaeaea', marginTop: 12, marginBottom: 6, fontWeight: '600' },
  input: {
    backgroundColor: '#16213e',
    color: '#eaeaea',
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#0f3460',
  },
  chipRow: { flexDirection: 'row', marginBottom: 4 },
  chip: {
    backgroundColor: '#16213e',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#0f3460',
  },
  chipActive: { backgroundColor: '#e94560', borderColor: '#e94560' },
  chipText: { color: '#eaeaea', fontSize: 13, fontWeight: '500' },
  chipTextActive: { color: '#fff' },
  button: {
    backgroundColor: '#e94560',
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '700' },
  spacer: { height: 60 },
});