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

if __name__=='__main__':unittest.main()
