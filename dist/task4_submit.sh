#!/bin/bash -l
# Upload together with task4_batch.py beside the existing cluster_config.json.
set -eo pipefail
here=${2:-$(cd -- "$(dirname -- "$0")" && pwd)}
module load anaconda3
conda activate myenv
set -u
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1
export MPLBACKEND=Agg PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
exec python -B -u "$here/task4_batch.py" "${1:---submit}" --directory "$here"
