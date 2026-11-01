import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd


class SubjectAnalysisTests(unittest.TestCase):
    def test_selection_is_per_person_and_preserves_all_activities(self):
        from empirical.task7_subjects import select_first_windows
        meta=pd.DataFrame({'subject_id':[2,1,1,2,1,2], 'activity_id':[1,1,1,1,2,2],
                           'split':['train']*6,'source_row':[5,3,1,2,8,7],
                           'array_index':range(6)})
        selected=select_first_windows(meta,[1,2])
        self.assertEqual(selected.array_index.tolist(),[2,3,4,5])
        self.assertFalse(selected.duplicated(['activity_id','subject_id']).any())

    def test_direct_cross_statistic_and_shared_input(self):
        from empirical.task7_subjects import evaluate_group,array_hash
        Y=np.random.default_rng(15).normal(size=(9,3,24))
        with tempfile.TemporaryDirectory() as d:
            rows=evaluate_group(Y,activity_id=1,activity_name='WALKING',seed=9,B=13,alpha=.05,output=Path(d))
            self.assertEqual(len(rows),4)
            self.assertEqual({r['input_sha256'] for r in rows},{array_hash(Y)})
            C=np.cov(Y.reshape(len(Y),-1),rowvar=False)
            mask=np.repeat(np.repeat(~np.eye(3,dtype=bool),24,0),24,1)
            T=np.sqrt(len(Y))*np.abs(C[mask]).max()
            self.assertAlmostEqual(rows[0]['T'],T)
            boot=np.load(Path(d)/'bootstrap.npy')
            self.assertEqual(rows[0]['p_value'],(1+(boot>=T).sum())/14)
            self.assertEqual(rows[0]['observation_unit'],'real_subject')

    def test_one_method_failure_does_not_remove_other_methods(self):
        from empirical.task7_subjects import evaluate_group
        Y=np.random.default_rng(18).normal(size=(8,2,24))
        with tempfile.TemporaryDirectory() as d:
            with patch('empirical.task7_subjects.covariance_one_sample',side_effect=ValueError('test failure')):
                rows=evaluate_group(Y,activity_id=1,activity_name='WALKING',seed=9,B=13,alpha=.05,output=Path(d))
            self.assertEqual(rows[0]['status'],'failed')
            self.assertIsNone(rows[0]['p_value'])
            self.assertIsNone(rows[0]['reject'])
            self.assertEqual([r['status'] for r in rows[1:]],['ok']*3)

    def test_checkpoint_rejects_changed_input_or_artifact(self):
        from empirical.task7_subjects import validate_checkpoint,file_hash
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'result.json';p.write_text('[]')
            checkpoint={'identity':{'source':'first'},'artifacts':{'result.json':file_hash(p)}}
            validate_checkpoint(checkpoint,{'source':'first'},Path(d))
            with self.assertRaisesRegex(ValueError,'identity'):
                validate_checkpoint(checkpoint,{'source':'second'},Path(d))
            p.write_text('[1]')
            with self.assertRaisesRegex(ValueError,'artifact'):
                validate_checkpoint(checkpoint,{'source':'first'},Path(d))

    def test_aggregate_identity_is_not_relabelled_as_single_activity(self):
        from empirical.task7_subjects import evaluate_group
        Y=np.random.default_rng(31).normal(size=(8,2,24))
        with tempfile.TemporaryDirectory() as d:
            rows=evaluate_group(Y,activity_id=0,activity_name='STATIC_SUBJECT_MEAN',seed=9,B=13,
                alpha=.05,output=Path(d),analysis_id='static_subject_mean',branch='subject_aggregate',
                representation='Across all activity 4/5/6 source windows within each true subject')
            self.assertEqual({r['analysis_id'] for r in rows},{'static_subject_mean'})
            self.assertEqual({r['branch'] for r in rows},{'subject_aggregate'})


if __name__=='__main__':
    unittest.main()
