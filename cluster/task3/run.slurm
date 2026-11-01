#!/bin/bash -l
# Resource/account/log directives are supplied by the login-node controller.
release=$1
output=$2
stage=$3
phase=${4:-pilot}
cd -- "$release" || exit $?
module load anaconda3 || exit $?
conda activate myenv || exit $?
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1
export MPLBACKEND=Agg PYTHONUNBUFFERED=1
python -c 'import sys,numpy,scipy,pandas,matplotlib,tqdm; assert sys.version_info[:3] == (3,9,25),sys.version; assert numpy.__version__ == "2.0.2",numpy.__version__; assert scipy.__version__ == "1.13.1",scipy.__version__; print(sys.version); print(numpy.__version__,scipy.__version__,pandas.__version__,matplotlib.__version__,tqdm.__version__)'
args=("$stage" --output "$output")
case "$stage" in
    init|benchmark) [[ "${5:-false}" != true ]] || args+=(--skip-dimension-extension) ;;
    worker) args+=(--phase "$phase" --chunk-id "${SLURM_ARRAY_TASK_ID:?array index required}" --retry-failures) ;;
    collect|report) args+=(--phase "$phase") ;;
    plan-workers) args+=(--phase "$phase" --seconds-per-chunk "${5:?chunk budget required}") ;;
esac
python -u -m simulation.task3_experiments "${args[@]}"
