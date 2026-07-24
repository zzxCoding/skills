# zzxcodingskills

面向 Codex、Claude Code 及其他兼容 Agent Skills 的个人技能集合。

## 技能

### skill-description-translator

仅翻译 `SKILL.md` YAML frontmatter 中的 `description` 字段，保留技能名称、其他元数据与正文。

未提供目标路径时，会先发现当前项目和常见用户级技能目录，给出推荐选项，并保留手工路径入口：

```bash
python3 skills/skill-description-translator/scripts/translate_skill_descriptions.py \
  discover --project-root .
```

目录：

```text
skills/skill-description-translator/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── translate_skill_descriptions.py
└── tests/
    └── test_translate_skill_descriptions.py
```

本地安装：

```bash
npx skills add . --skill skill-description-translator
```

直接验证：

```bash
python3 -m unittest discover \
  -s skills/skill-description-translator/tests \
  -p 'test_*.py'
```

## 设计依据

- 遵循 [Agent Skills 规范](https://agentskills.io/specification)的 `SKILL.md` 与 YAML frontmatter 约定。
- 采用 [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)和 [Anthropic Skills](https://github.com/anthropics/skills)使用的 `skills/<name>/` 集合式目录。
- 把确定性的扫描与写入放在 `scripts/`，让 `SKILL.md` 聚焦工作流和行为边界。
