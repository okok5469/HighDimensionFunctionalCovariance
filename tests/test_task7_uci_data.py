import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd


class UCIDataTests(unittest.TestCase):
    def test_bad_bytes_and_incomplete_matrix_are_rejected(self):
        from empirical.task7_uci_data import read_numeric
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'signal.txt'
            path.write_bytes(b'1 2\x00\n')
            with self.assertRaisesRegex(ValueError,'NUL'):
                read_numeric(path,(1,2))
            path.write_bytes(b'1 2\n3 4\n')
            with self.assertRaisesRegex(ValueError,'shape'):
                read_numeric(path,(1,2))

    def test_integer_labels_never_truncate_fractional_values(self):
        from empirical.task7_uci_data import read_numeric
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'subject.txt';path.write_bytes(b'1\n2.5\n')
            with self.assertRaisesRegex(ValueError,'integer'):
                read_numeric(path,(2,),integer=True)

    def test_first_window_per_person_activity_is_stable_and_independent(self):
        from empirical.task7_uci_data import select_first_windows
        frame=pd.DataFrame([
            dict(global_index=4,subject_id=2,activity_id=1,split='test',source_row=12),
            dict(global_index=3,subject_id=1,activity_id=1,split='train',source_row=8),
            dict(global_index=2,subject_id=1,activity_id=1,split='train',source_row=3),
            dict(global_index=1,subject_id=2,activity_id=2,split='test',source_row=1),
        ])
        result=select_first_windows(frame)
        self.assertEqual(result.global_index.tolist(),[2,4,1])
        self.assertFalse(result.duplicated(['activity_id','subject_id']).any())


if __name__=='__main__':
    unittest.main()
