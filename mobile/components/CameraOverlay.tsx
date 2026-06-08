import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface CameraOverlayProps {
  detectedItems: string[];
  missingItems: string[];
  scanning: boolean;
}

export default function CameraOverlay({
  detectedItems,
  missingItems,
  scanning,
}: CameraOverlayProps) {
  if (!scanning && detectedItems.length === 0 && missingItems.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      {scanning && (
        <View style={styles.scanningBar}>
          <View style={styles.scanningDot} />
          <Text style={styles.scanningText}>Scanning...</Text>
        </View>
      )}
      {detectedItems.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✓ Detected</Text>
          {detectedItems.slice(0, 5).map((item, i) => (
            <Text key={i} style={styles.detectedItem}>
              {item}
            </Text>
          ))}
          {detectedItems.length > 5 && (
            <Text style={styles.more}>+{detectedItems.length - 5} more</Text>
          )}
        </View>
      )}
      {missingItems.length > 0 && (
        <View style={[styles.section, styles.missingSection]}>
          <Text style={styles.missingTitle}>⚠️ Still Missing</Text>
          {missingItems.slice(0, 5).map((item, i) => (
            <Text key={i} style={styles.missingItem}>
              {item}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 40,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(26, 26, 46, 0.92)',
    padding: 16,
    borderRadius: 12,
  },
  scanningBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  scanningDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#e94560',
    marginRight: 8,
  },
  scanningText: { color: '#e94560', fontSize: 14, fontWeight: '600' },
  section: { marginTop: 6 },
  sectionTitle: { color: '#4ecdc4', fontSize: 14, fontWeight: '700', marginBottom: 4 },
  detectedItem: { color: '#eaeaea', fontSize: 13, marginLeft: 8 },
  more: { color: '#888', fontSize: 12, marginLeft: 8, marginTop: 2 },
  missingSection: { marginTop: 10, borderTopWidth: 1, borderTopColor: '#3d0f0f', paddingTop: 8 },
  missingTitle: { color: '#e94560', fontSize: 14, fontWeight: '700', marginBottom: 4 },
  missingItem: { color: '#ff9999', fontSize: 13, marginLeft: 8 },
});