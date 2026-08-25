from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
RAW_DIR = ROOT / 'data' / 'raw'
PROCESSED_DIR = ROOT / 'data' / 'processed'
MODEL_DIR = ROOT / 'models'
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{ROOT / 'data' / 'airline_ops.db'}")
TARGET_SAMPLE_SIZE = int(os.getenv('TARGET_SAMPLE_SIZE', '75000'))
RANDOM_SEED = int(os.getenv('RANDOM_SEED', '42'))
