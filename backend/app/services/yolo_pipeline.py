"""YOLOv8n travel-item detection model training pipeline."""

from pathlib import Path

from app.config import settings


class YOLOTrainingPipeline:
    """Fine-tune YOLOv8n on travel-items dataset and export to ONNX."""

    def __init__(
        self,
        dataset_yaml: str | None = None,
        base_model: str = "yolov8n.pt",
        epochs: int = 100,
        imgsz: int = 640,
        batch_size: int = 16,
    ):
        self.dataset_yaml = dataset_yaml
        self.base_model = base_model
        self.epochs = epochs
        self.imgsz = imgsz
        self.batch_size = batch_size

    def create_dataset_yaml(
        self,
        dataset_dir: str,
        train_split: str = "train",
        val_split: str = "val",
        test_split: str = "test",
        num_classes: int = 250,
    ) -> str:
        """Create YOLO-format dataset.yaml for training."""
        classes = self._get_travel_item_classes()
        classes_yaml = "\n".join(f"  {i} {name}" for i, name in enumerate(classes[:num_classes]))

        yaml_content = f"""path: {dataset_dir}
train: {train_split}/images
val: {val_split}/images
test: {test_split}/images

nc: {min(num_classes, len(classes))}
names:
{classes_yaml}
"""
        output_path = Path(dataset_dir) / "dataset.yaml"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_content, encoding="utf-8")
        return str(output_path)

    def train(self, dataset_yaml: str | None = None, resume: bool = False) -> dict:
        """Fine-tune YOLOv8n on travel-items dataset.

        Uses transfer learning: freeze backbone, train detection head.
        """
        from ultralytics import YOLO

        yaml_path = dataset_yaml or self.dataset_yaml
        if not yaml_path:
            raise ValueError("dataset_yaml must be provided for training")

        model = YOLO(self.base_model)

        if not resume:
            model.model.parameters()

        results = model.train(
            data=yaml_path,
            epochs=self.epochs,
            imgsz=self.imgsz,
            batch=self.batch_size,
            freeze=10,
            patience=20,
            project="smart_baggage_travel",
            name="yolov8n_travel",
            exist_ok=resume,
            pretrained=True,
            optimizer="AdamW",
            lr0=0.001,
            warmup_epochs=5,
            cos_lr=True,
            augment=True,
            mosaic=1.0,
            mixup=0.1,
            copy_paste=0.1,
            degrees=15,
            translate=0.1,
            scale=0.5,
            fliplr=0.5,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4,
        )

        best_path = Path(results.save_dir) / "weights" / "best.pt"
        return {
            "status": "completed",
            "best_model_path": str(best_path),
            "epochs_trained": results.epochs,
            "final_metrics": {
                "mAP50": float(results.results_dict.get("metrics/mAP50(B)", 0)),
                "mAP50-95": float(results.results_dict.get("metrics/mAP50-95(B)", 0)),
                "precision": float(results.results_dict.get("metrics/precision(B)", 0)),
                "recall": float(results.results_dict.get("metrics/recall(B)", 0)),
            },
        }

    def validate(self, model_path: str | None = None, dataset_yaml: str | None = None) -> dict:
        """Validate a trained model on the validation set."""
        from ultralytics import YOLO

        path = model_path or settings.yolov8_pt_path
        model = YOLO(path)

        yaml_path = dataset_yaml or self.dataset_yaml
        if not yaml_path:
            raise ValueError("dataset_yaml required for validation")

        results = model.val(data=yaml_path, imgsz=self.imgsz, batch=self.batch_size)

        return {
            "mAP50": float(results.box.map50),
            "mAP50-95": float(results.box.map),
            "precision": float(results.box.mp),
            "recall": float(results.box.mr),
            "per_class_ap": {
                name: float(ap) for name, ap in zip(results.names.values(), results.box.ap50)
            },
        }

    def export_onnx(
        self,
        model_path: str | None = None,
        output_path: str | None = None,
        simplify: bool = True,
        half: bool = False,
        dynamic: bool = False,
        imgsz: int = 640,
    ) -> str:
        """Export trained model to ONNX format for mobile deployment."""
        from ultralytics import YOLO

        path = model_path or settings.yolov8_pt_path
        model = YOLO(path)

        export_path = model.export(
            format="onnx",
            simplify=simplify,
            half=half,
            dynamic=dynamic,
            imgsz=imgsz,
        )

        output = output_path or settings.yolov8_onnx_path
        Path(output).parent.mkdir(parents=True, exist_ok=True)

        import shutil
        shutil.copy2(str(export_path), output)

        return output

    def export_coreml(self, model_path: str | None = None, imgsz: int = 640) -> str:
        """Export trained model to CoreML format for iOS Neural Engine."""
        from ultralytics import YOLO

        path = model_path or settings.yolov8_pt_path
        model = YOLO(path)
        return str(model.export(format="coreml", imgsz=imgsz))

    def detect_from_image(
        self,
        image_path: str,
        model_path: str | None = None,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ) -> list[dict]:
        """Run inference on a single image (server-side)."""
        from ultralytics import YOLO

        path = model_path or settings.yolov8_pt_path
        if not Path(path).exists():
            path = "yolov8n.pt"

        model = YOLO(path)
        results = model.predict(
            source=image_path,
            conf=conf_threshold,
            iou=iou_threshold,
            verbose=False,
        )

        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    "class_id": int(box.cls),
                    "class_name": result.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox_xyxy": box.xyxy.tolist()[0] if box.xyxy.numel() > 0 else [],
                })

        return detections

    def _get_travel_item_classes(self) -> list[str]:
        """Return the 250 travel-item class names for training."""
        return [
            "tshirt", "dress_shirt", "polo", "jeans", "shorts", "skirt", "dress",
            "sweater", "hoodie", "jacket", "coat", "rain_jacket", "swimwear",
            "underwear", "socks", "scarf", "gloves", "hat", "beanie", "belt",
            "tie", "pajamas", "leggings", "thermal_top", "fleece_vest",
            "windbreaker", "blazer", "suit", "cardigan", "poncho", "sarong",
            "rash_guard", "cargo_pants", "chinos", "linen_pants", "down_vest",
            "puffer_jacket", "parka", "trench_coat", "peacoat", "vest",
            "phone_charger", "laptop_charger", "power_bank", "usb_cable",
            "hdmi_cable", "headphones", "earbuds", "laptop", "tablet",
            "e_reader", "camera", "gopro", "drone", "portable_speaker",
            "travel_adapter", "voltage_converter", "extension_cord",
            "portable_ssd", "sd_card", "flashlight", "headlamp",
            "electronic_toothbrush", "electronic_razor", "hair_dryer_travel",
            "curling_iron_travel", "steam_iron_travel", "portable_wifi",
            "passport", "boarding_pass", "visa_document", "travel_insurance",
            "driver_license", "vaccination_card", "hotel_confirmation",
            "itinerary", "emergency_contact", "credit_card", "currency",
            "toothbrush", "toothpaste", "shampoo_travel", "conditioner_travel",
            "body_wash_travel", "deodorant", "razor", "shaving_cream",
            "sunscreen", "lip_balm", "moisturizer", "face_wash",
            "contact_lens_case", "contact_solution", "glasses", "sunglasses",
            "nail_clippers", "tweezers", "first_aid_kit", "band_aids",
            "pain_reliever", "antihistamine", "motion_sickness_pills",
            "hand_sanitizer", "wet_wipes", "tissues", "menstrual_products",
            "hair_brush", "comb", "hair_ties", "dry_shampoo", "perfume_travel",
            "mouthwash_travel", "dental_floss", "cotton_swabs", "nail_file",
            "makeup_foundation", "mascara", "eyeliner", "lipstick",
            "eyeshadow_palette", "blush", "concealer", "makeup_brushes",
            "makeup_sponge", "makeup_remover", "insect_repellent",
            "after_sun_lotion", "blister_pads", "compression_socks",
            "eye_mask", "earplugs", "backpack", "duffel_bag", "packing_cubes",
            "luggage_lock", "luggage_tag", "travel_pillow", "neck_pillow",
            "blanket_travel", "water_bottle", "reusable_bag", "umbrella",
            "rain_cover", "trekking_poles", "carabiner", "clothesline_travel",
            "laundry_bag", "shoe_bag", "money_belt", "neck_wallet",
            "fanny_pack", "day_pack", "dry_bag", "stuff_sack",
            "microfiber_towel", "yoga_mat", "guidebook", "journal", "pen",
            "playing_cards", "binoculars", "snorkel_set", "goggles",
            "pocket_knife", "multitool", "hammock", "portable_fan",
            "hand_warmer", "duct_tape_mini", "safety_pins", "sewing_kit",
            "bubble_wrap", "sleeping_bag_liner", "camping_cup", "spork",
            "beach_mat", "picnic_blanket", "inflatable_pool_float",
            "waterproof_phone_case", "laptop_stand", "phone_stand",
            "wireless_charger", "car_charger", "battery_case",
            "fitness_tracker", "smart_watch", "portable_keyboard",
            "portable_mouse", "international_driving_permit",
            "student_id", "customs_declaration", "travel_check",
        ]


yolo_pipeline = YOLOTrainingPipeline()
