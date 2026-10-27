import importlib.util, json, tempfile, unittest
from pathlib import Path
SPEC = importlib.util.spec_from_file_location("scar_verify", Path(__file__).parents[1] / "scripts" / "scar_pqc_attest.py")
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
def record(payload, previous=None):
    item = dict(payload)
    if previous is not None: item["hash_prev"] = previous
    item["hash"] = MODULE.digest(item)
    return item
class ChainTests(unittest.TestCase):
    def check(self, items):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"records.jsonl"; p.write_text("".join(json.dumps(x)+"\n" for x in items),encoding="utf-8")
            return MODULE.verify(p)
    def test_single_record(self): self.assertTrue(self.check([record({"event":"genesis"})])[0])
    def test_valid_chain(self):
        first=record({"event":"one"}); second=record({"event":"two"},first["hash"])
        self.assertTrue(self.check([first,second])[0])
    def test_tamper_rejected(self):
        item=record({"event":"original"}); item["event"]="tampered"
        ok,msg=self.check([item]); self.assertFalse(ok); self.assertIn("hash mismatch",msg)
    def test_broken_link_rejected(self):
        first=record({"event":"one"}); second=record({"event":"two"},"f"*128)
        ok,msg=self.check([first,second]); self.assertFalse(ok); self.assertIn("hash_prev",msg)
    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"empty"; p.write_text("",encoding="utf-8")
            ok,msg=MODULE.verify(p); self.assertFalse(ok); self.assertIn("no SCAR records",msg)
if __name__ == "__main__": unittest.main()

import importlib.util,json,tempfile,unittest
from pathlib import Path
S=importlib.util.spec_from_file_location("scar",Path(__file__).parents[1]/"scripts"/"scar_pqc_attest.py")
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class GenesisTests(unittest.TestCase):
 def test_committed_genesis_hash(self):
  record=json.loads((Path(__file__).parents[1]/"SCAR.jsonl").read_text(encoding="utf-8"))
  self.assertEqual(record["hash"],M.digest(record))
 def test_committed_genesis_verifies(self):
  ok,msg=M.verify(Path(__file__).parents[1]/"SCAR.jsonl")
  self.assertTrue(ok,msg)
