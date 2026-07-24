---
name: skill-description-translator
description: 将一个或多个 Agent Skill 的 SKILL.md YAML frontmatter 中的英文 description 翻译为简体中文，同时保持 name、其他元数据和 Markdown 正文不变。用户要求翻译技能描述、本地化 Claude Code、Codex 或其他兼容 Agent Skills 的技能，或批量处理技能目录时使用。
---

# Skill Description Translator

只本地化 `SKILL.md` frontmatter 的 `description` 字段。使用随附脚本确定性地扫描和写入文件，由当前代理完成翻译。

## 核心契约

- 只修改 YAML frontmatter 中的顶层 `description`。
- 不修改 `name`、其他 frontmatter 字段、Markdown 正文或其他文件。
- 保留 SVG、HTML、API、CLI、框架名称和命令等技术术语。
- 保留原文的功能范围、触发条件和确定性，不添加不存在的能力。
- 写入前必须展示 dry-run 差异并获得用户确认。

## 工作流

### 1. 确定目标或提供选项

用户已指定单个 `SKILL.md` 或目录时，直接使用该路径。

用户没有指定路径时，不要只要求用户手工输入。先运行：

```bash
python3 scripts/translate_skill_descriptions.py discover \
  --project-root <current-project>
```

根据 JSON 结果列出已发现的目录，并把 `recommended: true` 的目录放在第一项。例如：

1. 当前项目的 `skills/`（推荐，发现 8 个技能）
2. Codex 用户技能目录（发现 14 个技能）
3. Claude Code 用户技能目录（发现 6 个技能）
4. 手工输入其他路径

请用户回复编号；若客户端支持结构化选项，优先使用结构化选择。即使只发现一个目录，也同时提供“手工输入其他路径”。若没有发现任何目录，说明已检查的位置，再请用户输入特殊路径。

### 2. 扫描技能

从本技能目录运行：

```bash
python3 scripts/translate_skill_descriptions.py scan <target>
```

检查 JSON 输出：

- `language_hint: no-cjk`：候选英文描述。
- `language_hint: contains-cjk`：可能已经是中文，默认跳过并向用户说明。
- `status: error`：缺少描述、frontmatter 无效或存在重复字段；不要直接修改。

向用户列出发现的技能，并确认本轮要翻译的范围。用户已明确指定全部技能时，无需再次询问范围。

如果目标中没有任何 `no-cjk` 候选项，不要以“请提供目标路径”结束。运行 `discover`，改为提供其他已发现目录和“手工输入其他路径”选项。

### 3. 生成翻译映射

逐项翻译候选描述，并创建 UTF-8 JSON 文件。键必须使用扫描输出中的相对路径，值为完整译文：

```json
{
  "architecture-diagram/SKILL.md": "创建专业的架构图。用户要求系统架构、基础设施或网络拓扑图时使用。"
}
```

翻译时：

- 使用自然、专业、简洁的简体中文。
- 同时保留“做什么”和“何时触发”两类信息。
- 保持枚举、范围限定、否定条件和文件类型不变。
- 不翻译唯一标识符、路径、代码、命令或产品名。
- 不把概括改写成更强的承诺。

### 4. 预览差异

```bash
python3 scripts/translate_skill_descriptions.py apply <target> \
  --translations <translations.json>
```

命令默认不写文件。检查 JSON 中的 `diff`，确认每个差异都只位于 `description` 字段。

### 5. 确认并写入

只有用户确认 dry-run 后才执行：

```bash
python3 scripts/translate_skill_descriptions.py apply <target> \
  --translations <translations.json> \
  --write
```

脚本会原子替换文件，并保持未目标字段与正文不变。

### 6. 验证并报告

再次执行 `scan`，确认译文存在且没有解析错误。若环境提供 Agent Skills 校验器，再运行对应校验；不要为了校验擅自安装依赖。

最终报告：

- 已翻译的技能和路径。
- 每项原文与译文。
- 跳过项及原因。
- 验证结果和未验证边界。

## 边界情况

- 没有 `description`：跳过并报告。
- 已包含中文：默认跳过，除非用户明确要求重译。
- 多行 YAML 标量：保留原有 `|` 或 `>` 风格。
- 只读文件或写入失败：保留原文件并继续处理其他目标。
- 译文为空、超过 1024 个字符或包含 NUL：拒绝写入并报告。
