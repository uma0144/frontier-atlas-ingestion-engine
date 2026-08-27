"""
Configuration module for GraphOne / FrontierAtlas Intelligence Ingestion Engine.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure output directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API Keys (Optional with mock / direct fallback)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Optional, enhances GitHub API rate limits

# Crawler Settings
DEFAULT_CONCURRENCY = int(os.getenv("CONCURRENCY", "15"))
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "15"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Rate Limiting & 429 backoff
INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 30.0
BACKOFF_FACTOR = 2.0
JITTER_RANGE = (0.1, 0.5)

# LLM Chunking Limits (Anti-413)
MAX_CHUNK_TOKENS = 4000
MAX_HTML_CHARS = 12000

# Target Collection Counts
TARGET_PAPERS_COUNT = 1000
TARGET_STARTUPS_COUNT = 1000
TARGET_PRODUCTS_COUNT = 1000
MAX_NEWS_HOURS = 24
MAX_JOB_HOURS = 24

# Output Filepaths
EXCEL_OUTPUT_PATH = OUTPUT_DIR / "frontier_atlas_intelligence.xlsx"
PDF_OUTPUT_PATH = BASE_DIR / "architecture.pdf"
