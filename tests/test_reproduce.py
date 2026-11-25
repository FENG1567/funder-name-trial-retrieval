import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reproduce as r

class ScientificRules(unittest.TestCase):
    def test_nonestimable_is_not_zero(self):
        self.assertIsNone(r.percentage(0,0))
        self.assertEqual(r.percentage(0,4),0.0)
        self.assertIsNone(r.difference(0,0,6,27))
        with self.assertRaises(ValueError):
            r.percentage(3,2)

    def test_difference_uses_unrounded_fractions(self):
        observed=r.difference(10,12,21,25)
        self.assertAlmostEqual(observed,-2/3)
        self.assertEqual(round(observed,1),-0.7)
        self.assertAlmostEqual(r.difference(27,27,53,58),500/58)

    def test_family_union_is_not_identifier_count(self):
        links=[{'family_id':'A','A_known_identifier_hit':'True'},
               {'family_id':'A','A_known_identifier_hit':'True'},
               {'family_id':'B','A_known_identifier_hit':'False'},
               {'family_id':'B','A_known_identifier_hit':'True'}]
        self.assertEqual(r.family_union(links),{'A','B'})

    def test_explicit_boolean_and_missing(self):
        self.assertFalse(r.truth('False'))
        self.assertTrue(r.truth('TRUE'))
        with self.assertRaises(ValueError):
            r.truth('')
        with self.assertRaises(ValueError):
            r.truth('Not estimable')

    def test_registry_end_cutoff_inclusive(self):
        self.assertTrue(r.historical_mrc_eligible('2022-12-31 00:00:00'))
        self.assertFalse(r.historical_mrc_eligible('2023-01-01 00:00:00'))

    def test_multiple_ids_do_not_define_row_count(self):
        self.assertEqual(r.identifiers('NCT00000001; NCT00000002; NCT00000001'),{'NCT00000001','NCT00000002'})
        self.assertEqual(len(r.count_fraction([{'IDs':'NCT00000001;NCT00000002'}],lambda row: True)),2)
        self.assertEqual(r.count_fraction([{'IDs':'NCT00000001;NCT00000002'}],lambda row: True),[1,1])

    def test_inputs_match_reported_comparisons(self):
        with tempfile.TemporaryDirectory() as directory:
            result=r.run(Path(directory),figures=False)
            self.assertTrue(result['passed'])

if __name__=='__main__':
    unittest.main()
