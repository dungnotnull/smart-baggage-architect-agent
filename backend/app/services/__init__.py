"""Services package -- re-export singletons."""

from app.services.airline_policy import AirlinePolicyEngine, policy_engine
from app.services.airline_scraper import AirlinePolicyScraper, airline_scraper
from app.services.bin_packing import BinPackingService, bin_packing_service
from app.services.clip_fallback import CLIPFallbackService, clip_fallback_service
from app.services.database import DatabaseService, db_service
from app.services.feedback import FeedbackService, feedback_service
from app.services.knapsack import KnapsackOptimizer, knapsack_optimizer
from app.services.knowledge_crawler import KnowledgeCrawlerService, knowledge_crawler
from app.services.llm_orchestrator import LLMOrchestrator, llm_orchestrator
from app.services.logger import app_logger
from app.services.packing_list import PackingListGenerator, packing_generator
from app.services.weather import WeatherService, weather_service
from app.services.yolo_pipeline import YOLOTrainingPipeline, yolo_pipeline

__all__ = [
    "AirlinePolicyEngine",
    "AirlinePolicyScraper",
    "BinPackingService",
    "CLIPFallbackService",
    "DatabaseService",
    "FeedbackService",
    "KnapsackOptimizer",
    "KnowledgeCrawlerService",
    "LLMOrchestrator",
    "PackingListGenerator",
    "WeatherService",
    "YOLOTrainingPipeline",
    "airline_scraper",
    "bin_packing_service",
    "clip_fallback_service",
    "db_service",
    "feedback_service",
    "knapsack_optimizer",
    "knowledge_crawler",
    "llm_orchestrator",
    "packing_generator",
    "policy_engine",
    "weather_service",
    "yolo_pipeline",
    "app_logger",
]
