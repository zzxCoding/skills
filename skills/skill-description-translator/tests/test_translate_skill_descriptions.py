from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "translate_skill_descriptions.py"
)


class TranslateSkillDescriptionsTest(unittest.TestCase):
    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

    def write_skill(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_translations(self, root: Path, payload: dict[str, str]) -> Path:
        path = root / "translations.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def test_scan_reports_language_hints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_skill(
                root,
                "english",
                "---\nname: english\ndescription: Translate skill metadata.\n---\n\n# English\n",
            )
            self.write_skill(
                root,
                "chinese",
                "---\nname: chinese\ndescription: 翻译技能元数据。\n---\n\n# Chinese\n",
            )

            result = self.run_script("scan", str(root))

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            hints = {
                item["path"]: item["language_hint"] for item in payload["skills"]
            }
            self.assertEqual(hints["english/SKILL.md"], "no-cjk")
            self.assertEqual(hints["chinese/SKILL.md"], "contains-cjk")

    def test_discover_offers_ranked_project_and_user_options(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            user_home = root / "user"
            self.write_skill(
                project / "skills",
                "project-skill",
                "---\nname: project-skill\ndescription: 项目技能。\n---\n",
            )
            self.write_skill(
                user_home / ".codex" / "skills",
                "user-skill",
                "---\nname: user-skill\ndescription: User skill.\n---\n",
            )

            result = self.run_script(
                "discover",
                "--project-root",
                str(project),
                "--home-root",
                str(user_home),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["manual_path_allowed"])
            self.assertEqual(len(payload["candidates"]), 2)
            self.assertEqual(payload["candidates"][0]["scope"], "user")
            self.assertEqual(
                payload["candidates"][0]["translatable_descriptions"], 1
            )
            self.assertTrue(payload["candidates"][0]["recommended"])
            self.assertEqual(payload["candidates"][1]["scope"], "project")
            self.assertEqual(payload["candidates"][1]["already_localized"], 1)
            self.assertFalse(payload["candidates"][1]["recommended"])

    def test_apply_is_dry_run_by_default_and_preserves_comment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = self.write_skill(
                root,
                "sample",
                "---\n"
                "name: sample\n"
                'description: "Translate descriptions." # keep\n'
                "license: MIT\n"
                "---\n\n"
                "# Body\n",
            )
            original = skill.read_text(encoding="utf-8")
            translations = self.write_translations(
                root, {"sample/SKILL.md": "翻译技能描述。"}
            )

            result = self.run_script(
                "apply",
                str(root),
                "--translations",
                str(translations),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(skill.read_text(encoding="utf-8"), original)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "dry-run")
            self.assertIn(
                'description: "翻译技能描述。" # keep',
                payload["changes"][0]["diff"],
            )

    def test_write_changes_only_inline_description(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = self.write_skill(
                root,
                "sample",
                "---\n"
                "name: sample\n"
                "description: Translate descriptions.\n"
                "metadata:\n"
                "  owner: example\n"
                "---\n\n"
                "# Body\n\n"
                "Keep this body unchanged.\n",
            )
            translations = self.write_translations(
                root, {"sample/SKILL.md": "翻译技能描述。"}
            )

            result = self.run_script(
                "apply",
                str(root),
                "--translations",
                str(translations),
                "--write",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                skill.read_text(encoding="utf-8"),
                "---\n"
                "name: sample\n"
                "description: 翻译技能描述。\n"
                "metadata:\n"
                "  owner: example\n"
                "---\n\n"
                "# Body\n\n"
                "Keep this body unchanged.\n",
            )

    def test_write_preserves_block_scalar_style(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = self.write_skill(
                root,
                "sample",
                "---\n"
                "name: sample\n"
                "description: |-\n"
                "  Translate descriptions.\n"
                "  Use for Agent Skills.\n"
                "license: MIT\n"
                "---\n\n"
                "# Body\n",
            )
            translations = self.write_translations(
                root,
                {
                    "sample/SKILL.md": (
                        "翻译技能描述。\n适用于 Agent Skills。"
                    )
                },
            )

            result = self.run_script(
                "apply",
                str(root),
                "--translations",
                str(translations),
                "--write",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = skill.read_text(encoding="utf-8")
            self.assertIn(
                "description: |-\n"
                "  翻译技能描述。\n"
                "  适用于 Agent Skills。\n",
                updated,
            )
            self.assertTrue(updated.endswith("---\n\n# Body\n"))

    def test_unknown_translation_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_skill(
                root,
                "sample",
                "---\nname: sample\ndescription: Translate descriptions.\n---\n",
            )
            translations = self.write_translations(
                root, {"missing/SKILL.md": "翻译技能描述。"}
            )

            result = self.run_script(
                "apply",
                str(root),
                "--translations",
                str(translations),
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "error")


if __name__ == "__main__":
    unittest.main()
