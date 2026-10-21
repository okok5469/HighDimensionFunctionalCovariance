from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
import os

# Paths are resolved relative to the project root.

from archive.stock_empirical.empirical_data_loader import prepare_empirical_data
from archive.stock_empirical.empirical_main import sanity_check

cache = f'{STOCK_CACHE_DIR}/empirical_data.pkl'
if os.path.exists(cache):
    os.remove(cache)

try:
    data = prepare_empirical_data(n=200, p=50, M=48, q=5)
    print('Y_smooth', data['Y_smooth'].shape)
    print('symbols', len(data['symbols']))
    print('names', len(data['names']))
    print('mean_corr', sanity_check(data))
except Exception as e:
    import traceback
    traceback.print_exc()
