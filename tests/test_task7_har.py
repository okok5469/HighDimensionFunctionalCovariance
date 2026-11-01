import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from empirical import task7_har as har


class Task7Tests(unittest.TestCase):
    def test_strict_loader_axes_and_bad_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'raw.csv'
            rows = [(i,t,*[i*100+t*10+j for j in range(6)]) for i in [4,2] for t in range(128)]
            pd.DataFrame(rows,columns=['sample_id','time',*[f'var_{j}' for j in range(6)]]).to_csv(p,index=False)
            _,Y=har.strict_dynamic(p)
            self.assertEqual(Y.shape,(2,6,128))
            self.assertEqual(Y[0,3,9],293)
            p.write_bytes(b'broken\x00')
            with self.assertRaisesRegex(ValueError,'NUL'):
                har.strict_dynamic(p)

    def test_complete_cross_blocks_and_identity(self):
        a=np.arange(24,dtype=float).reshape(2,3,4)
        self.assertNotEqual(har.array_hash(a),har.array_hash(a+1))
        mask=har.cross_mask(3,4)
        self.assertEqual(mask.shape,(12,12))
        self.assertFalse(mask[:4,:4].any())
        self.assertTrue(mask[:4,4:8].all())

    def test_four_methods_shared_input_and_direct_statistic(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            Y=np.random.default_rng(7).normal(size=(12,3,24))
            result=har.evaluate(Y,seed=9,B=17,alpha=.05,output=out)
            self.assertEqual(len(result),4)
            self.assertEqual(len({r['input_sha256'] for r in result}),1)
            C=np.cov(Y.reshape(12,-1),rowvar=False)
            expected=np.sqrt(12)*np.abs(C[har.cross_mask(3,24)]).max()
            self.assertAlmostEqual(result[0]['T'],expected)
            boot=np.load(out/'bootstrap.npy')
            self.assertEqual(result[0]['p_value'],(1+(boot>=expected).sum())/18)

    def test_changed_artifact_invalidates_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);p=root/'artifact';p.write_bytes(b'first')
            identity=har.file_hash(p)
            self.assertTrue(har.valid_artifacts({'artifact':identity},root))
            p.write_bytes(b'second')
            self.assertFalse(har.valid_artifacts({'artifact':identity},root))
