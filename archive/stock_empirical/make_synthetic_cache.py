from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common.paths import STOCK_CACHE_DIR, STOCK_RESULTS_DIR
from archive.stock_empirical.empirical_data_loader import build_synthetic_empirical_data, demarket, fourier_smooth
import pickle, os
os.makedirs(str(STOCK_CACHE_DIR), exist_ok=True)
res = build_synthetic_empirical_data(n=200, p=200, M=48, q=5, seed=0)
# apply demarket
res['Y_std'] = demarket(res['Y_std'])
res['Y_smooth'], res['a'], res['phi'] = fourier_smooth(res['Y_std'], q=5)
path = f'{STOCK_CACHE_DIR}/empirical_data_n200_p200_M48_q5_demarket1.pkl'
with open(path, 'wb') as f:
    pickle.dump(res, f)
print('WROTE', path)
