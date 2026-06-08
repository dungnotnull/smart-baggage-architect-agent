/**
 * Type declarations for external modules without TypeScript definitions.
 */

declare module 'react-native-vision-camera' {
  import { ComponentType, Ref } from 'react';

  export type CameraPosition = 'front' | 'back';

  export interface CameraDevice {
    id: string;
    name: string;
    position: CameraPosition;
    sensorOrientation: number;
    formats: any[];
  }

  export interface Photo {
    path: string;
    width: number;
    height: number;
    isRawPhoto: boolean;
  }

  export interface TakePhotoOptions {
    qualityPrioritization: 'quality' | 'speed' | 'balanced';
    flash?: 'on' | 'off' | 'auto';
  }

  export interface CameraProps {
    device: CameraDevice;
    isActive: boolean;
    photo?: boolean;
    video?: boolean;
    style?: any;
    ref?: Ref<any>;
    takePhoto?: (options: TakePhotoOptions) => Promise<Photo>;
  }

  export const Camera: ComponentType<CameraProps>;

  export function useCameraDevices(position?: CameraPosition): CameraDevice[];
}

declare module 'onnxruntime-react-native' {
  export class Tensor {
    constructor(type: string, data: ArrayLike<number>, dims: number[]);
    data: ArrayLike<number>;
    dims: number[];
    type: string;
  }

  export interface InferenceSession {
    run(feeds: Record<string, Tensor>): Promise<Record<string, Tensor>>;
    release(): Promise<void>;
    outputNames: string[];
  }

  export interface SessionOptions {
    executionProviders?: string[];
  }

  export const InferenceSession: {
    create(path: string, options?: SessionOptions): Promise<InferenceSession>;
  };
}