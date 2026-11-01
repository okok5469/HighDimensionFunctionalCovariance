#!/bin/bash -l
# A finite compute stage; account, budget and dependency are supplied by sbatch.
release=$1
output=$2
stage=$3
cd -- "$release" || exit $?
module load anaconda3 || exit $?
conda activate myenv || exit $?
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1
export MPLBACKEND=Agg PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
python -B -c 'import sys,numpy,scipy; assert sys.version_info[:3] == (3, 9, 25),sys.version; assert numpy.__version__ == "2.0.2",numpy.__version__; assert scipy.__version__ == "1.13.1",scipy.__version__; print(sys.version,numpy.__version__,scipy.__version__)'
exec python -B -u "$release/cluster/task5/controller.py" "$stage" --release "$release" --output "$output"
