"""Download ML models for smart-baggage-architect.

Usage:
    python scripts/download_models.py --all
    python scripts/download_models.py --yolo
    python scripts/download_models.py --clip
    python scripts/download_models.py --phi3
"""

import argparse
import shutil
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def download_yolo():
    """Download YOLOv8n base model (will be fine-tuned later)."""
    from ultralytics import YOLO

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("Downloading YOLOv8n base model...")
    model = YOLO("yolov8n.pt")
    save_path = MODELS_DIR / "yolov8n.pt"
    shutil.copy2("yolov8n.pt", str(save_path))
    print(f"YOLOv8n saved to {save_path}")
    print("NOTE: This is the base model. Fine-tune on travel-items dataset using the training pipeline.")


def download_clip():
    """Download CLIP ViT-B/32 model for zero-shot fallback."""
    from transformers import CLIPModel, CLIPProcessor

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    clip_dir = MODELS_DIR / "clip-vit-base-patch32"
    print("Downloading CLIP ViT-B/32...")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor.save_pretrained(str(clip_dir))
    model.save_pretrained(str(clip_dir))
    print(f"CLIP saved to {clip_dir}")


def download_phi3():
    """Download Phi-3-mini-4k-instruct Q4_K_M GGUF for local LLM."""
    print("Downloading Phi-3-mini GGUF...")
    print("This model is ~2.2 GB. Download from HuggingFace:")
    print("  https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf")
    print("  File: phi3-mini-4k-instruct-q4.gguf")
    print(f"  Save to: {MODELS_DIR / 'phi3-mini-q4.gguf'}")
    print("")
    print("Or use huggingface-cli:")
    print(f"  huggingface-cli download microsoft/Phi-3-mini-4k-instruct-gguf "
          f"phi3-mini-4k-instruct-q4.gguf --local-dir {MODELS_DIR}")
    print("")
    print("NOTE: Due to the large size, GGUF models must be downloaded manually.")


def main():
    parser = argparse.ArgumentParser(description="Download ML models")
    parser.add_argument("--all", action="store_true", help="Download all models")
    parser.add_argument("--yolo", action="store_true", help="Download YOLOv8n base model")
    parser.add_argument("--clip", action="store_true", help="Download CLIP ViT-B/32")
    parser.add_argument("--phi3", action="store_true", help="Download Phi-3-mini GGUF")
    args = parser.parse_args()

    if args.all or args.yolo:
        download_yolo()
    if args.all or args.clip:
        download_clip()
    if args.all or args.phi3:
        download_phi3()

    if not (args.all or args.yolo or args.clip or args.phi3):
        parser.print_help()


if __name__ == "__main__":
    main()