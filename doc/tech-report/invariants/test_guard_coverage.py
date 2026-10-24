"""Coverage must stay red when classifications outnumber measured effects."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('coverage_gate',HERE/'check_guard_coverage.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class CoverageTests(unittest.TestCase):
    def test_classification_alone_is_not_evidence(self):
        result=gate.coverage(HERE)
        self.assertEqual(result['proven'],0)
        self.assertEqual(result['unresolved'],138)
        self.assertFalse(result['passed'])

    def test_measured_subset_does_not_close_all_guards(self):
        result=gate.coverage(HERE,HERE/'evidence/guard-operations.json')
        self.assertEqual(result['proven'],43)
        self.assertEqual(result['unresolved'],95)
        self.assertFalse(result['passed'])

    def test_failed_native_value_is_rejected(self):
        data=json.loads((HERE/'evidence/guard-operations.json').read_text())
        data['rows'][0]['observed'][0]=-1
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.json';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError,'Numerical effect failed'):
                gate.coverage(HERE,path)

    def test_missing_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            for name in ['guard-inventory.json','guard-classification.json']:
                shutil.copyfile(HERE/name,dest/name)
            p=dest/'guard-classification.json';data=json.loads(p.read_text());data['rows'].pop(0);p.write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError,'Original candidate omitted'):
                gate.coverage(dest)

    def test_dtype_specific_constants_are_exercised(self):
        manifest=json.loads((HERE/'guard-source-fixtures.json').read_text())
        native_float={f['name'] for f in manifest['fixtures'] if f.get('input_dtype')=='float32'}
        self.assertTrue({'float32-normal-floor','float32-subnormal-floor','float32-negative-power'}<=native_float)

    def test_all_source_operations_have_measured_effects(self):
        result=gate.coverage(HERE,HERE/'evidence/guard-operations.json',HERE/'evidence/guard-source-effects.json')
        self.assertEqual(result['proven'],138)
        self.assertEqual(result['unresolved'],0)
        self.assertTrue(result['passed'])

    def check_bad_source(self, change, message):
        data=json.loads((HERE/'evidence/guard-source-effects.json').read_text())
        change(data)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad-source.json';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError,message):
                gate.coverage(HERE,HERE/'evidence/guard-operations.json',path)

    def test_missing_source_fixture_is_rejected(self):
        self.check_bad_source(lambda data:data['results'].pop(),'Missing source fixture')

    def test_source_numeric_failure_is_not_hidden_by_pass_label(self):
        self.check_bad_source(lambda data:data['results'][0]['observed'].__setitem__(0,-1.),'Source effect numerical mismatch')

    def test_nonfinite_source_result_is_rejected(self):
        self.check_bad_source(lambda data:data['results'][0]['observed'].__setitem__(0,float('nan')),'Source effect numerical mismatch')

    def test_forged_expected_value_is_rejected(self):
        self.check_bad_source(lambda data:data['results'][0]['expected'].__setitem__(0,-1.),'Expected value mismatch')

    def test_changed_source_fragment_is_rejected(self):
        self.check_bad_source(lambda data:data['results'][0]['fragments'][0].__setitem__('source_text','return true;'),'Fragment identity mismatch')

if __name__=='__main__':unittest.main()
