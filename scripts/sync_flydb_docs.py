#!/usr/bin/env python3
"""同步版本匹配的 Flydb 参考；手写工作流和历史版本说明不做全局替换。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from urllib.parse import quote, urlsplit
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = Path("skills/flydb-cli-release/references")
DOCUMENTS = {
    **{f"docs/reference/{name}.md": f"{name}.md" for name in (
        "commands", "configuration", "errors", "json-output", "mcp-tools", "web-api",
    )},
    "docs/getting-started/web.md": "web.md",
    "docs/getting-started/jdbc-integration.md": "jdbc-integration.md",
    "docs/design/11-plan-artifact.md": "plan-artifact.md",
}
# 这些文件需要人工合并到四个技能的职责中；记录哈希以发现下一次上游变化。
WATCH_SOURCES = (
    "pom.xml",
    "flydb-skills/skills/flydb-cli/SKILL.md",
    "docs/getting-started/multi-environment.md",
)
MANIFEST = REFERENCE_DIR / "upstream-sync.json"
LINK = re.compile(r"(?P<start>!?\[[^\]\n]*\]\()(?P<url>[^\s)]+)(?P<end>\))")


def git(source, *args):
    result = subprocess.run(
        ["git", "-C", str(source), *args], capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError(f"无法读取 Flydb Git 来源：{' '.join(args)}")
    return result.stdout.rstrip("\n")


def read_version(pom):
    root = ET.fromstring(pom)
    ns = {"m": "http://maven.apache.org/POM/4.0.0"} if root.tag.startswith("{") else {}
    prefix = "m:" if ns else ""
    version = root.findtext(f"{prefix}properties/{prefix}revision", namespaces=ns)
    if not version:
        version = root.findtext(f"{prefix}version", namespaces=ns)
    version = (version or "").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", version):
        raise ValueError("无法从根 pom.xml 的 revision/version 解析版本号")
    return version


def rewrite_links(content, source_path, commit):
    def replace(match):
        url = match["url"]
        if url.startswith(("#", "/")) or urlsplit(url).scheme:
            return match[0]
        path, sep, fragment = url.partition("#")
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), path))
        if resolved in DOCUMENTS:
            target = DOCUMENTS[resolved]
        else:
            # 非运行必需的设计/数据库专页保留固定提交的来源链接。
            target = f"https://github.com/zzxCoding/Flydb/blob/{commit}/{quote(resolved)}"
        return match["start"] + target + (sep + fragment if sep else "") + match["end"]
    return LINK.sub(replace, content)


def adapt_document(content, source_path):
    adaptations = []
    # commands.md 明确 web 是长驻服务；上游 JSON 概述仍用“所有命令”。
    if source_path == "docs/reference/json-output.md":
        old = "`--json` 是全局选项，作用于所有命令，可与"
        if old in content:
            content = content.replace(old, "`--json` 是全局选项，适用于除 `web` 外的命令，可与", 1)
            adaptations.append("按 commands.md 补充 web 不支持 --json 的例外")
    if source_path == "docs/getting-started/jdbc-integration.md":
        if "flydb-cli-0.2.1" in content:
            content = content.replace("flydb-cli-0.2.1", "flydb-cli-${FLYDB_VERSION}")
            content = content.replace(
                "### 2.1 复用 MySQL/Oracle 家族\n",
                "### 2.1 复用 MySQL/Oracle 家族\n\n"
                "示例中的 `FLYDB_VERSION` 应设为已核验可用的发行版本；获取与校验见"
                "[发布包指南](release-package.md)。源码版本不代表已有公开 ZIP。\n", 1,
            )
            adaptations.append("历史 ZIP 示例改用已核验的 FLYDB_VERSION")
    return content, adaptations


def build_outputs(source):
    # 写入前读取全部输入：缺文件、坏版本、无 Git 来源时不产生半次同步。
    inputs = {path: (source / path).read_bytes() for path in (*DOCUMENTS, *WATCH_SOURCES)}
    version = read_version(inputs["pom.xml"])
    commit = git(source, "rev-parse", "HEAD")
    dirty = git(source, "status", "--porcelain", "--untracked-files=all", "--", *inputs)
    manifest = {
        "source_repository": "https://github.com/zzxCoding/Flydb",
        "source_commit": commit,
        "source_version": version,
        "source_inputs_dirty": bool(dirty),
        "source_input_status": dirty.splitlines(),
        "release_status": "not_verified",
        "documents": [],
        "manual_review_sources": [
            {"source": path, "sha256": hashlib.sha256(inputs[path]).hexdigest()}
            for path in WATCH_SOURCES
        ],
    }
    outputs = {}
    for path, destination in DOCUMENTS.items():
        content = inputs[path].decode("utf-8")
        # 在源路径空间转换链接，再加入本地补充链接。
        content = rewrite_links(content, path, commit)
        content, adaptations = adapt_document(content, path)
        title, separator, body = content.partition("\n")
        if not separator or not title.startswith("# "):
            raise ValueError(f"源文档缺少一级标题：{path}")
        header = (
            f"> 随 `flydb-cli-release` 打包，来源：Flydb `{path}`；源码版本 {version}，"
            f"提交 `{commit[:12]}`。来源是本地工作区快照，发布状态未核验；文件哈希与适配记录见"
            "[upstream-sync.json](upstream-sync.json)。使用目标发行包文档与 `--help` 核对版本差异。"
        )
        outputs[REFERENCE_DIR / destination] = f"{title}\n\n{header}\n\n{body.lstrip()}"
        manifest["documents"].append({
            "source": path,
            "destination": str(REFERENCE_DIR / destination),
            "sha256": hashlib.sha256(inputs[path]).hexdigest(),
            "adaptations": adaptations,
        })
    outputs[MANIFEST] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return outputs


def synchronize(source, destination, check=False):
    outputs = build_outputs(source)
    changes = [path for path, content in outputs.items()
               if not (destination / path).exists()
               or (destination / path).read_bytes() != content.encode("utf-8")]
    for path in changes:
        print(f"{'待同步' if check else '同步'} {path}")
    if check:
        return 1 if changes else 0
    for path in changes:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(outputs[path].encode("utf-8"))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path,
                        default=Path(os.environ.get("FLYDB_HOME", REPO_ROOT.parent / "Flydb")))
    parser.add_argument("--check", action="store_true", help="只读检查；有漂移返回 1，不写文件")
    args = parser.parse_args()
    try:
        code = synchronize(args.source.expanduser().resolve(), REPO_ROOT, args.check)
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"同步失败：{exc}", file=sys.stderr)
        return 2
    print("请另行对比上游 SKILL.md 与多环境指南，维护四个入口、手写参考和 evals；"
          "本工具不更新这些文件，也不核验公开发行或安装技能。")
    return code


if __name__ == "__main__":
    sys.exit(main())
