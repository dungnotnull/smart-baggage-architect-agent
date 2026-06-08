import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  DimensionValue,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Camera, useCameraDevices } from 'react-native-vision-camera';
import type { CameraDevice } from 'react-native-vision-camera';
import api from '../services/api';
import { yoloScanner, YOLODetection } from '../services/yoloScanner';

export default function CameraScanScreen() {
  const { tripId } = useLocalSearchParams<{ tripId: string }>();
  const router = useRouter();
  const cameraRef = useRef<any>(null);
  const devices = useCameraDevices('back');
  const device: CameraDevice | undefined = devices.find(d => d.position === 'back') || devices[0];

  const [detectedItems, setDetectedItems] = useState<YOLODetection[]>([]);
  const [scanning, setScanning] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [matchedCount, setMatchedCount] = useState(0);
  const [packedCount, setPackedCount] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [modelReady, setModelReady] = useState(false);
  const [lastScanTime, setLastScanTime] = useState<string | null>(null);
  const scanInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    (async () => {
      const loaded = await yoloScanner.loadModel();
      setModelReady(loaded);
    })();
    return () => {
      yoloScanner.release();
      if (scanInterval.current) clearInterval(scanInterval.current);
    };
  }, []);

  useEffect(() => {
    if (!tripId) return;
    (async () => {
      const { data } = await api.getPackingList(tripId);
      if (data) {
        const items = (data as any).packing_list?.items || [];
        setTotalItems(items.length);
        setPackedCount(items.filter((i: any) => i.packed).length);
      }
    })();
  }, [tripId]);

  const startScanning = useCallback(() => {
    setCameraActive(true);
    setScanning(true);
    setDetectedItems([]);
    setMatchedCount(0);

    if (modelReady) {
      scanInterval.current = setInterval(async () => {
        try {
          const photo = await cameraRef.current?.takePhoto?.({
            qualityPrioritization: 'speed',
            flash: 'off',
          });

          if (photo) {
            const result = await yoloScanner.scanFrame(
              photo.path,
              photo.width,
              photo.height
            );
            if (result.detections.length > 0) {
              setDetectedItems(result.detections);
              setLastScanTime(new Date().toLocaleTimeString());
            }
          }
        } catch {
          // Frame capture or inference error - continue scanning
        }
      }, 500);
    } else {
      // Fallback: use server-side YOLO detection via API
      serverSideScan();
    }
  }, [modelReady]);

  const serverSideScan = useCallback(async () => {
    if (!tripId) return;
    try {
      // Prompt user to take a photo and upload for server-side detection
      const photo = await cameraRef.current?.takePhoto?.({
        qualityPrioritization: 'quality',
        flash: 'auto',
      });

      if (photo && photo.path) {
        const { data, error } = await api.detectItems(photo.path);
        if (error) {
          Alert.alert('Scan Error', error);
        } else if (data) {
          const detected = (data as any).detected_items || [];
          const scores = (data as any).confidence_scores || [];
          const detections: YOLODetection[] = detected.map(
            (name: string, idx: number) => ({
              className: name,
              confidence: scores[idx] || 0.5,
              bbox: [0.1, 0.1, 0.5, 0.5],
            })
          );
          setDetectedItems(detections);
          setLastScanTime(new Date().toLocaleTimeString());
        }
      } else {
        // Camera not available, show info about server-side detection
        Alert.alert(
          'Server Detection Mode',
          'Take a photo of your suitcase contents and upload it for server-side YOLO detection. This requires an active internet connection.'
        );
      }
    } catch {
      Alert.alert('Scan Error', 'Could not connect to server for detection.');
    } finally {
      setScanning(false);
    }
  }, [tripId]);

  const stopScanning = useCallback(() => {
    setCameraActive(false);
    setScanning(false);
    if (scanInterval.current) {
      clearInterval(scanInterval.current);
      scanInterval.current = null;
    }
  }, []);

  const handleMarkDetected = useCallback(
    async (className: string) => {
      if (!tripId) return;
      const { data } = await api.getPackingList(tripId);
      if (data) {
        const items = (data as any).packing_list?.items || [];
        const match = items.find(
          (i: any) =>
            !i.packed &&
            (i.name.toLowerCase().includes(className.toLowerCase()) ||
              className.toLowerCase().includes(i.name.toLowerCase()))
        );
        if (match) {
          await api.markItemDetected(tripId, match.id);
          setMatchedCount((c) => c + 1);
          setPackedCount((c) => c + 1);
          Alert.alert('Detected & Packed', match.name + ' checked off!');
        }
      }
    },
    [tripId]
  );

  const renderDetectedItem = ({ item }: { item: YOLODetection }) => {
    const confidencePct = Math.round(item.confidence * 100);
    return (
      <TouchableOpacity
        style={styles.detectedRow}
        onPress={() => handleMarkDetected(item.className)}
      >
        <View style={styles.detectedLeft}>
          <Text style={styles.detectedName}>{item.className}</Text>
          <View style={styles.confidenceRow}>
            <View
              style={[
                styles.confidenceBar,
                { width: confidencePct as DimensionValue },
              ]}
            />
            <Text style={styles.detectedConf}>
              {confidencePct}%
            </Text>
          </View>
        </View>
        <Text style={styles.tapToMark}>&#10003; Mark</Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Camera Scan</Text>

      <View style={styles.summaryRow}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryValue}>{detectedItems.length}</Text>
          <Text style={styles.summaryLabel}>Detected</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={[styles.summaryValue, { color: '#4ecdc4' }]}>{matchedCount}</Text>
          <Text style={styles.summaryLabel}>Matched</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryValue}>{packedCount}/{totalItems}</Text>
          <Text style={styles.summaryLabel}>Packed</Text>
        </View>
      </View>

      <View style={styles.cameraView}>
        {cameraActive && device ? (
          <Camera
            ref={cameraRef}
            style={styles.camera}
            device={device}
            isActive={cameraActive}
            photo={true}
          />
        ) : (
          <View style={styles.cameraPlaceholder}>
            <Text style={styles.cameraIcon}>&#128247;</Text>
            <Text style={styles.cameraLabel}>
              {modelReady ? 'Tap Start to scan with YOLOv8n' : 'Camera ready \u2014 server detection mode'}
            </Text>
          </View>
        )}
        {scanning && (
          <View style={styles.scanningOverlay}>
            <ActivityIndicator size="large" color="#e94560" />
            <Text style={styles.scanningText}>Scanning...</Text>
          </View>
        )}
      </View>

      <View style={styles.controls}>
        {!scanning ? (
          <TouchableOpacity style={styles.scanButton} onPress={startScanning}>
            <Text style={styles.scanButtonText}>&#9654; Start Scan</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={[styles.scanButton, styles.stopButton]} onPress={stopScanning}>
            <Text style={styles.scanButtonText}>&#9632; Stop</Text>
          </TouchableOpacity>
        )}
      </View>

      {lastScanTime && (
        <Text style={styles.scanTime}>Last scan: {lastScanTime}</Text>
      )}

      {detectedItems.length > 0 && (
        <>
          <Text style={styles.detectedTitle}>
            Detected ({detectedItems.length})
          </Text>
          <FlatList
            data={detectedItems}
            keyExtractor={(item, i) => item.className + i}
            renderItem={renderDetectedItem}
            style={styles.detectedList}
          />
        </>
      )}

      <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
        <Text style={styles.backButtonText}>&#8592; Back to Packing List</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e', padding: 16 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#e94560', marginBottom: 12 },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  summaryItem: { alignItems: 'center' },
  summaryValue: { fontSize: 22, fontWeight: '700', color: '#eaeaea' },
  summaryLabel: { fontSize: 11, color: '#888', marginTop: 2 },
  cameraView: {
    borderRadius: 16,
    height: 260,
    overflow: 'hidden',
    marginBottom: 12,
    backgroundColor: '#0f3460',
  },
  camera: { flex: 1 },
  cameraPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cameraIcon: { fontSize: 40, marginBottom: 8 },
  cameraLabel: { color: '#eaeaea', fontSize: 14, fontWeight: '600', textAlign: 'center' },
  scanningOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanningText: { color: '#e94560', fontSize: 16, fontWeight: '600', marginTop: 10 },
  controls: { flexDirection: 'row', justifyContent: 'center', marginBottom: 8 },
  scanButton: {
    backgroundColor: '#e94560',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 10,
  },
  stopButton: { backgroundColor: '#555' },
  scanButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  scanTime: { color: '#888', fontSize: 12, textAlign: 'center', marginBottom: 8 },
  detectedTitle: { color: '#4ecdc4', fontSize: 18, fontWeight: '700', marginBottom: 8 },
  detectedList: { maxHeight: 200 },
  detectedRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#16213e',
    padding: 12,
    borderRadius: 8,
    marginBottom: 6,
    borderLeftWidth: 3,
    borderLeftColor: '#4ecdc4',
  },
  detectedLeft: { flex: 1 },
  detectedName: { color: '#eaeaea', fontSize: 16, fontWeight: '500', marginBottom: 4 },
  confidenceRow: { flexDirection: 'row', alignItems: 'center' },
  confidenceBar: {
    height: 4,
    backgroundColor: '#4ecdc4',
    borderRadius: 2,
    marginRight: 8,
    maxWidth: 80,
  },
  detectedConf: { color: '#888', fontSize: 12 },
  tapToMark: { color: '#4ecdc4', fontSize: 12, fontWeight: '600' },
  backButton: {
    backgroundColor: '#16213e',
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#0f3460',
  },
  backButtonText: { color: '#eaeaea', fontSize: 16, fontWeight: '600' },
});