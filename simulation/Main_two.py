"""Compatibility entry for M2; use --profile formal for full experiments."""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulation import covariance_experiments as runner

# The compatibility API executes serially. Frozen counts live in each profile.
USE_PARALLEL = False
NUM_PROCESSES = 1
TEST_MODE = True
OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'results' / 'validation_v1.1_20261021' / 'M2'


def create_experiment_tasks():
    profile = 'smoke' if TEST_MODE else 'formal'
    return [dict(task) for task in runner.load_config(profile)['tasks']
            if task['model'] == 'M2']


def execute_single_task(task):
    config = dict(task)
    config.setdefault('model', 'M2')
    config['with_xue'] = True
    return runner.execute_single_task(config)


def save_partial_results(results, experiment_num):
    return runner.save_partial_results(results, experiment_num, OUTPUT_DIR)


def run_experiment():
    return runner.run_tasks(create_experiment_tasks(), OUTPUT_DIR)


if __name__ == '__main__':
    runner.main(model='M2')
