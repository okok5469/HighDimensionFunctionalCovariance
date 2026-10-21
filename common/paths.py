"""Locate inputs and outputs relative to the project, independent of cwd."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAR_DATA_DIR = PROJECT_ROOT / 'data' / 'har'
SIMULATION_RESULTS_DIR = PROJECT_ROOT / 'results' / 'simulation'
HAR_RESULTS_DIR = PROJECT_ROOT / 'results' / 'empirical' / 'har'
STOCK_CACHE_DIR = PROJECT_ROOT / 'data' / 'cache' / 'stock'
STOCK_RESULTS_DIR = PROJECT_ROOT / 'results' / 'empirical' / 'stock'
