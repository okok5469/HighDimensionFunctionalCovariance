"""Task-card acceptance checks, using independent output coverage requirements."""
import unittest
from pathlib import Path


class DeliveryTests(unittest.TestCase):
    def test_all_requested_statistical_panels_are_defined(self):
        from plot_statistics import figure_plan
        plan = figure_plan()
        self.assertEqual(plan['fig01_confirm_size'], 20)
        self.assertEqual(plan['fig02_confirm_power'], 60)
        self.assertEqual(plan['fig03_paired_differences'], 27)
        self.assertEqual(plan['figS01_all_confirm_pairs'], 45)


if __name__ == '__main__':
    unittest.main()
