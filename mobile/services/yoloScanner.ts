/**
 * YOLOv8n ONNX camera scanner bridge.
 *
 * On-device inference pipeline:
 * 1. react-native-vision-camera captures frames
 * 2. Frame is converted to RGB tensor (640x640)
 * 3. ONNX Runtime Mobile runs YOLOv8n inference
 * 4. Post-processing: NMS + class mapping
 * 5. Results returned to JS for UI overlay
 *
 * When ONNX Runtime React Native package is installed:
 *   npm install onnxruntime-react-native
 *
 * When YOLO model (.onnx) is deployed to app assets:
 *   Copy models/yolov8n-travel.onnx to mobile/assets/models/
 */

import { Platform } from 'react-native';

const TRAVEL_ITEM_CLASSES = [
  'passport', 'boarding_pass', 'phone_charger', 'power_bank', 'usb_cable',
  'travel_adapter', 'earbuds', 'toothbrush', 'toothpaste', 'sunscreen',
  'tshirt', 'underwear', 'socks', 'pants', 'shorts', 'jacket', 'sweater',
  'swimwear', 'rain_jacket', 'pajamas', 'belt', 'hat', 'scarf', 'gloves',
  'shampoo', 'deodorant', 'razor', 'lip_balm', 'hand_sanitizer', 'wet_wipes',
  'backpack', 'packing_cubes', 'luggage_lock', 'umbrella', 'water_bottle',
  'neck_pillow', 'laundry_bag', 'shoe_bag', 'money_belt', 'journal',
  'laptop', 'tablet', 'camera', 'headphones', 'glasses', 'sunglasses',
  'wallet', 'keys', 'watch', 'book', 'pen',
];

const MODEL_INPUT_SIZE = 640;
const CONFIDENCE_THRESHOLD = 0.5;
const NMS_IOU_THRESHOLD = 0.45;

export interface YOLODetection {
  className: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2] normalized 0-1
}

export interface YOLOScanResult {
  detections: YOLODetection[];
  frameWidth: number;
  frameHeight: number;
  timestamp: number;
}

/**
 * YOLOv8 ONNX Scanner - handles frame capture, inference, and post-processing.
 */
class YOLOScanner {
  private session: any = null;
  private modelLoaded = false;

  /**
   * Load YOLOv8n ONNX model for inference.
   * Must be called before scan().
   */
  async loadModel(modelPath?: string): Promise<boolean> {
    try {
      const ort = require('onnxruntime-react-native');
      const path = modelPath || this.getDefaultModelPath();
      this.session = await ort.InferenceSession.create(path, {
        executionProviders: [Platform.OS === 'ios' ? 'coreml' : 'nnapi', 'cpu'],
      });
      this.modelLoaded = true;
      return true;
    } catch (err) {
      console.warn('ONNX Runtime not available, falling back to server detection:', err);
      this.modelLoaded = false;
      return false;
    }
  }

  /**
   * Run inference on an image frame.
   */
  async scanFrame(imageData: Uint8Array, width: number, height: number): Promise<YOLOScanResult> {
    if (!this.modelLoaded || !this.session) {
      throw new Error('Model not loaded. Call loadModel() first.');
    }

    const ort = require('onnxruntime-react-native');

    // Pre-process: resize to 640x640, normalize to [0,1], NCHW format
    const tensor = this.preprocess(imageData, width, height);
    const feeds = { images: tensor };
    const results = await this.session.run(feeds);

    // Post-process: parse YOLO output, apply NMS
    const outputKey = this.session.outputNames[0];
    const output = results[outputKey];
    const detections = this.postprocess(output, width, height);

    return {
      detections,
      frameWidth: width,
      frameHeight: height,
      timestamp: Date.now(),
    };
  }

  /**
   * Pre-process image data for YOLOv8 input.
   * Expects RGBA Uint8Array, outputs Float32 NCHW tensor [1,3,640,640].
   */
  private preprocess(imageData: Uint8Array, width: number, height: number): any {
    const ort = require('onnxruntime-react-native');
    const size = MODEL_INPUT_SIZE;
    const data = new Float32Array(3 * size * size);
    const scaleX = width / size;
    const scaleY = height / size;

    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const srcX = Math.floor(x * scaleX);
        const srcY = Math.floor(y * scaleY);
        const srcIdx = (srcY * width + srcX) * 4; // RGBA
        const dstIdx = y * size + x;

        // Normalize to [0,1] and arrange in CHW
        data[0 * size * size + dstIdx] = (imageData[srcIdx] || 0) / 255.0;     // R
        data[1 * size * size + dstIdx] = (imageData[srcIdx + 1] || 0) / 255.0; // G
        data[2 * size * size + dstIdx] = (imageData[srcIdx + 2] || 0) / 255.0; // B
      }
    }

    return new ort.Tensor('float32', data, [1, 3, size, size]);
  }

  /**
   * Post-process YOLOv8 output: extract boxes, apply NMS, map to class names.
   */
  private postprocess(output: any, origWidth: number, origHeight: number): YOLODetection[] {
    const data = output.data as Float32Array;
    const dims = output.dims as number[];

    // YOLOv8 output shape: [1, num_detections, 4+num_classes]
    // dims = [1, 84, 8400] for COCO (80 classes) or [1, N+4, 8400]
    const numDetections = dims[2] || 8400;
    const numClasses = (dims[1] || 84) - 4;

    const detections: Array<{
      className: string;
      confidence: number;
      x1: number;
      y1: number;
      x2: number;
      y2: number;
    }> = [];

    for (let i = 0; i < numDetections; i++) {
      // Find max class score
      let maxClassScore = 0;
      let maxClassIdx = 0;
      for (let c = 0; c < numClasses; c++) {
        const score = data[(4 + c) * numDetections + i];
        if (score > maxClassScore) {
          maxClassScore = score;
          maxClassIdx = c;
        }
      }

      if (maxClassScore < CONFIDENCE_THRESHOLD) continue;

      // Extract bounding box (cx, cy, w, h format in YOLOv8)
      const cx = data[0 * numDetections + i];
      const cy = data[1 * numDetections + i];
      const w = data[2 * numDetections + i];
      const h = data[3 * numDetections + i];

      const className = TRAVEL_ITEM_CLASSES[maxClassIdx] || `item_`+maxClassIdx;

      detections.push({
        className,
        confidence: maxClassScore,
        x1: (cx - w / 2) / MODEL_INPUT_SIZE,
        y1: (cy - h / 2) / MODEL_INPUT_SIZE,
        x2: (cx + w / 2) / MODEL_INPUT_SIZE,
        y2: (cy + h / 2) / MODEL_INPUT_SIZE,
      });
    }

    // NMS (Non-Maximum Suppression)
    const nmsDetections = this.nms(detections, NMS_IOU_THRESHOLD);

    return nmsDetections;
  }

  /**
   * Non-Maximum Suppression to remove overlapping detections.
   */
  private nms(
    detections: Array<{
      className: string;
      confidence: number;
      x1: number;
      y1: number;
      x2: number;
      y2: number;
    }>,
    iouThreshold: number
  ): YOLODetection[] {
    detections.sort((a, b) => b.confidence - a.confidence);
    const keep: YOLODetection[] = [];
    const suppressed = new Set<number>();

    for (let i = 0; i < detections.length; i++) {
      if (suppressed.has(i)) continue;
      const det = detections[i];
      keep.push({
        className: det.className,
        confidence: det.confidence,
        bbox: [det.x1, det.y1, det.x2, det.y2],
      });

      for (let j = i + 1; j < detections.length; j++) {
        if (suppressed.has(j)) continue;
        if (this.iou(det, detections[j]) > iouThreshold) {
          suppressed.add(j);
        }
      }
    }

    return keep;
  }

  /**
   * Calculate Intersection over Union for two bounding boxes.
   */
  private iou(
    a: { x1: number; y1: number; x2: number; y2: number },
    b: { x1: number; y1: number; x2: number; y2: number }
  ): number {
    const ix1 = Math.max(a.x1, b.x1);
    const iy1 = Math.max(a.y1, b.y1);
    const ix2 = Math.min(a.x2, b.x2);
    const iy2 = Math.min(a.y2, b.y2);
    const inter = Math.max(0, ix2 - ix1) * Math.max(0, iy2 - iy1);
    const areaA = (a.x2 - a.x1) * (a.y2 - a.y1);
    const areaB = (b.x2 - b.x1) * (b.y2 - b.y1);
    return inter / (areaA + areaB - inter + 1e-6);
  }

  /**
   * Get the default model path based on platform.
   */
  private getDefaultModelPath(): string {
    if (Platform.OS === 'android') {
      return 'file:///android_asset/models/yolov8n-travel.onnx';
    }
    return 'models/yolov8n-travel.onnx';
  }

  /**
   * Check if the model is loaded and ready.
   */
  isReady(): boolean {
    return this.modelLoaded;
  }

  /**
   * Release model resources.
   */
  async release(): Promise<void> {
    if (this.session) {
      await this.session.release();
      this.session = null;
      this.modelLoaded = false;
    }
  }
}

export const yoloScanner = new YOLOScanner();
export default yoloScanner;