"""Vision API endpoints — YOLO detection and CLIP fallback."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.packing import CLIPClassificationRequest, VisionDetectionResult

router = APIRouter()


@router.post("/detect", response_model=VisionDetectionResult)
async def detect_items_in_image(file: UploadFile = File(...)) -> VisionDetectionResult:
    """Detect travel items in an uploaded image using YOLOv8n."""
    import tempfile
    from pathlib import Path

    from app.services.yolo_pipeline import yolo_pipeline

    suffix = Path(file.filename or "image.jpg").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        detections = yolo_pipeline.detect_from_image(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    detected_items = [d["class_name"] for d in detections]
    confidence_scores = [d["confidence"] for d in detections]

    return VisionDetectionResult(
        detected_items=detected_items,
        confidence_scores=confidence_scores,
        unmatched_items=[],
        frame_timestamp=0.0,
    )


@router.post("/clip-classify")
async def clip_classify(request: CLIPClassificationRequest) -> list[dict]:
    """Classify an image using CLIP zero-shot when YOLO doesn't recognize items."""
    from app.services.clip_fallback import clip_fallback_service
    try:
        return clip_fallback_service.classify(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLIP classification error: {e}")


@router.post("/train")
async def start_training(
    dataset_yaml: str = "",
    epochs: int = 100,
    base_model: str = "yolov8n.pt",
) -> dict:
    """Start YOLOv8n fine-tuning (long-running, run in background)."""
    import asyncio

    from app.services.yolo_pipeline import YOLOTrainingPipeline

    pipeline = YOLOTrainingPipeline(
        dataset_yaml=dataset_yaml or None,
        base_model=base_model,
        epochs=epochs,
    )

    try:
        async def _train():
            return pipeline.train(dataset_yaml or None)

        result = await asyncio.to_thread(
            pipeline.train, dataset_yaml or None
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {e}")


@router.post("/export-onnx")
async def export_onnx(model_path: str = "") -> dict:
    """Export a trained model to ONNX format."""
    from app.services.yolo_pipeline import yolo_pipeline
    try:
        output = yolo_pipeline.export_onnx(model_path or None)
        return {"onnx_path": output, "status": "exported"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")
