"""执行文档中的两个 CI 阶段；使用假 CLI，绝不连接数据库。"""

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "skills/flydb-multi-environment/references/multi-environment.md"
FAKE_CLI = '''import json, os, sys
from pathlib import Path
args = sys.argv[1:]
command = next(x for x in args if x in ("version", "info", "validate", "migrate"))
is_plan = "--dry-run" in args
action = "plan" if is_plan else command
with Path(os.environ["CALL_LOG"]).open("a") as log:
    log.write(action + "\\n")
if os.environ.get("FAIL_ACTION") == action:
    print(json.dumps({"protocolVersion": 1, "status": "error", "exitCode": 2}))
    sys.exit(2)
result = {"protocolVersion": 1, "status": "success", "exitCode": 0}
if is_plan:
    result.update(dryRun=True, plan={"algorithm": "flydb-plan-v1", "id": os.environ["PLAN_ID"]})
print(json.dumps(result))
'''


@unittest.skipUnless(shutil.which("jq"), "文档示例需要 jq")
class CiExamplesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        (self.cwd / "bin").mkdir()
        (self.cwd / "fake.py").write_text(FAKE_CLI)
        cli = self.cwd / "bin/flydb"
        cli.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " "
                       + shlex.quote(str(self.cwd / "fake.py")) + ' "$@"\n')
        cli.chmod(0o700)
        self.log = self.cwd / "calls"
        self.env = dict(os.environ, TMPDIR=str(self.cwd), CALL_LOG=str(self.log), PLAN_ID="a" * 64)
        section = REFERENCE.read_text().split("## 5.", 1)[1].split("## 6.", 1)[0]
        self.preflight, self.apply = re.findall(r"```bash\n(.*?)\n```", section, re.S)

    def run_stage(self, script):
        return subprocess.run(["sh", "-c", script], cwd=self.cwd, env=self.env,
                              capture_output=True, text=True, timeout=30)

    def prepare(self):
        result = self.run_stage(self.preflight)
        self.assertEqual(result.returncode, 0, result.stderr)
        directory = next(self.cwd.glob("flydb-review.*"))
        self.env.update(ARTIFACT_DIR=str(directory), CONF="/opt/deploy/deploy/flydb.dm.prod.conf")

    def test_preflight_never_writes_database(self):
        self.prepare()
        self.assertEqual(self.log.read_text().splitlines(), ["version", "info", "validate", "plan"])

    def test_cli_failure_stops_preflight_before_plan(self):
        self.env["FAIL_ACTION"] = "validate"
        self.assertEqual(self.run_stage(self.preflight).returncode, 2)
        self.assertEqual(self.log.read_text().splitlines(), ["version", "info", "validate"])

    def test_changed_plan_blocks_migrate(self):
        self.prepare()
        self.env["PLAN_ID"] = "b" * 64
        self.assertEqual(self.run_stage(self.apply).returncode, 2)
        self.assertNotIn("migrate", self.log.read_text().splitlines())

    def test_approved_plan_executes_then_verifies(self):
        self.prepare()
        result = self.run_stage(self.apply)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines()[-4:], ["plan", "migrate", "info", "validate"])
        after = Path(self.env["ARTIFACT_DIR"]) / "after-validate.json"
        self.assertEqual(json.loads(after.read_text())["status"], "success")

    def test_migrate_failure_preserves_exit_code_and_stops_followups(self):
        self.prepare()
        self.env["FAIL_ACTION"] = "migrate"
        self.assertEqual(self.run_stage(self.apply).returncode, 2)
        self.assertEqual(self.log.read_text().splitlines()[-2:], ["plan", "migrate"])


if __name__ == "__main__":
    unittest.main()
