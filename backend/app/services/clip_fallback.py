"""Server-side CLIP zero-shot fallback for unknown items."""

import io

from PIL import Image

from app.models.packing import CLIPClassificationRequest, CLIPClassificationResult


class CLIPFallbackService:
    """Classify items using CLIP zero-shot when YOLO doesn't recognize them."""

    def __init__(self):
        self._model = None
        self._processor = None

    def _load_model(self):
        """Lazy-load CLIP model and processor."""
        from transformers import CLIPModel, CLIPProcessor

        model_id = "openai/clip-vit-base-patch32"
        self._processor = CLIPProcessor.from_pretrained(model_id)
        self._model = CLIPModel.from_pretrained(model_id)

    def classify(self, request: CLIPClassificationRequest) -> list[CLIPClassificationResult]:
        """Classify an image against candidate labels using CLIP.

        Args:
            request: CLIPClassificationRequest with image and labels

        Returns:
            List of CLIPClassificationResult sorted by score descending
        """
        if self._model is None:
            self._load_model()

        image = Image.open(io.BytesIO(request.image_base64.encode("latin1")))
        text_inputs = [f"a photo of a {label}" for label in request.candidate_labels]

        inputs = self._processor(
            text=text_inputs,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        outputs = self._model(**inputs)
        logits = outputs.logits_per_image.squeeze()
        probs = logits.softmax(dim=0)

        results = []
        for idx in range(len(request.candidate_labels)):
            score = probs[idx].item()
            results.append(CLIPClassificationResult(
                label=request.candidate_labels[idx],
                score=round(score, 4),
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:request.top_k]

    def classify_image_bytes(
        self,
        image_bytes: bytes,
        candidate_labels: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """Classify raw image bytes against candidate labels."""
        if self._model is None:
            self._load_model()

        image = Image.open(io.BytesIO(image_bytes))
        text_inputs = [f"a photo of a {label}" for label in candidate_labels]

        inputs = self._processor(
            text=text_inputs,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        outputs = self._model(**inputs)
        logits = outputs.logits_per_image.squeeze()
        probs = logits.softmax(dim=0)

        results = []
        for idx in range(len(candidate_labels)):
            results.append({
                "label": candidate_labels[idx],
                "score": round(probs[idx].item(), 4),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


clip_fallback_service = CLIPFallbackService()
