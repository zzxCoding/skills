import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "sync_flydb_docs.py"
SPEC = importlib.util.spec_from_file_location("sync_flydb_docs", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


class SyncFlydbDocsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "Flydb source"
        self.target = Path(self.temp.name) / "skills target"
        self.target.mkdir()
        for path in (*sync.DOCUMENTS, *sync.WATCH_SOURCES):
            file = self.source / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("# Example\n\nBody.\n", encoding="utf-8")
        (self.source / "pom.xml").write_text(
            '<project xmlns="http://maven.apache.org/POM/4.0.0">'
            '<version>${revision}</version><properties>'
            '<revision>0.3.6-SNAPSHOT</revision></properties></project>', encoding="utf-8",
        )
        self.git_patch = patch.object(sync, "git", side_effect=lambda root, *args:
                                     "a" * 40 if args[0] == "rev-parse" else " M pom.xml")
        self.git_patch.start()
        self.addCleanup(self.git_patch.stop)

    def run_sync(self, check=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync.synchronize(self.source, self.target, check)

    def snapshot(self, root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def test_check_reports_drift_without_writing(self):
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertEqual(self.snapshot(self.target), {})

    def test_sync_is_idempotent_and_preserves_handwritten_files_and_source(self):
        handwritten = self.target / "skills/flydb/SKILL.md"
        handwritten.parent.mkdir(parents=True)
        handwritten.write_bytes(b"Historical version 0.2.0 stays.\n")
        source_before = self.snapshot(self.source)
        self.assertEqual(self.run_sync(), 0)
        first = self.snapshot(self.target)
        mtimes = {p: p.stat().st_mtime_ns for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(self.run_sync(check=True), 0)
        self.assertEqual(first, self.snapshot(self.target))
        self.assertEqual(source_before, self.snapshot(self.source))
        self.assertTrue(all(p.stat().st_mtime_ns == t for p, t in mtimes.items()))
        self.assertEqual(handwritten.read_bytes(), b"Historical version 0.2.0 stays.\n")

    def test_missing_source_cannot_partially_overwrite_existing_output(self):
        self.run_sync()
        before = self.snapshot(self.target)
        (self.source / "docs/reference/commands.md").write_text("# Changed\n\nNew.\n")
        (self.source / "docs/design/11-plan-artifact.md").unlink()
        with self.assertRaises(FileNotFoundError):
            self.run_sync()
        self.assertEqual(before, self.snapshot(self.target))

    def test_manifest_records_dirty_source_and_does_not_claim_release(self):
        self.run_sync()
        manifest = json.loads((self.target / sync.MANIFEST).read_text())
        self.assertEqual(manifest["source_version"], "0.3.6-SNAPSHOT")
        self.assertTrue(manifest["source_inputs_dirty"])
        self.assertEqual(manifest["release_status"], "not_verified")
        self.assertEqual(len(manifest["documents"]), len(sync.DOCUMENTS))
        for document in manifest["documents"]:
            self.assertEqual(len(document["sha256"]), 64)

    def test_changed_workflow_source_is_detected_by_check(self):
        self.run_sync()
        before = self.snapshot(self.target)
        (self.source / sync.WATCH_SOURCES[1]).write_text("# New workflow\n\nReview me.\n")
        self.assertEqual(self.run_sync(check=True), 1)
        self.assertEqual(before, self.snapshot(self.target))

    def test_links_resolve_locally_or_to_pinned_upstream(self):
        content = "[json](../reference/json-output.md#载荷) [design](../design/example.md) [web](https://example.com)"
        output = sync.rewrite_links(content, "docs/getting-started/web.md", "a" * 40)
        self.assertIn("(json-output.md#载荷)", output)
        self.assertIn("https://github.com/zzxCoding/Flydb/blob/" + "a" * 40 + "/docs/design/example.md", output)
        self.assertIn("[web](https://example.com)", output)

    def test_root_version_fallback_does_not_select_dependency_version(self):
        self.assertEqual(sync.read_version(
            b"<project><version>0.3.6</version><dependencies><dependency>"
            b"<version>9.9.9</version></dependency></dependencies></project>"), "0.3.6")
        with self.assertRaises(ValueError):
            sync.read_version(b"<project><version>${unknown}</version></project>")


if __name__ == "__main__":
    unittest.main()
