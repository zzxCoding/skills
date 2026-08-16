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

### flydb-cli-release

使用 [Flydb](https://github.com/zzxCoding/Flydb) CLI 发布包完成数据库迁移的自包含技能：Java 环境预检、获取与验证发行包（已有安装 → 本地 ZIP → GitHub/Gitee Release 下载）、init、info、validate、`--dry-run migrate`、migrate、baseline、repair、undo、clean 与 JDBC 驱动接入。

技能自带命令、配置、错误码等全部参考文档（`references/`），复制到任何 Agent 技能目录都可独立工作，不依赖 GitHub 文档链接；参考对应 CLI 0.2.0，与 `--help` 实际输出不一致时以后者为准。

目录：

```text
skills/flydb-cli-release/
├── SKILL.md
├── references/
│   ├── commands.md          # CLI 命令参考（移植自 Flydb docs）
│   ├── configuration.md     # 配置项参考（移植自 Flydb docs）
│   ├── errors.md            # 错误码/退出码参考（移植自 Flydb docs）
│   ├── release-package.md   # 发布包获取、安装与 Java 运行环境
│   └── drivers.md           # JDBC 驱动解析与 FLYDB-1003 排查
└── evals/
    └── evals.json
```

本地安装：

```bash
npx skills add . --skill flydb-cli-release
```

### flydb-migration-scripts

管理使用 Flydb 的项目中的迁移脚本目录（`db/migration` 及自定义 locations）：新增 `V__`/`R__`/`U__` 脚本、命名与版本策略（递增整数/日期版本/目录版本）、子目录组织、占位符使用，以及 checksum 与失败记录的修改纪律（已应用的版本化脚本绝不改写，变更用新版本承载）。

自带命名规则与错误处置参考；执行 CLI 命令（migrate/repair 等）由 `flydb-cli-release` 技能覆盖，两者可独立使用。

目录：

```text
skills/flydb-migration-scripts/
├── SKILL.md
├── references/
│   ├── naming-and-versions.md     # 命名、版本规则与三类脚本语义
│   └── errors-and-discipline.md   # 修改红线与脚本目录相关错误码处置
└── evals/
    └── evals.json
```

本地安装：

```bash
npx skills add . --skill flydb-migration-scripts
```

### flydb-multi-environment

组织 Flydb 多数据库、多环境（测试/预发/生产）的迁移自动化：`deploy/` 配置矩阵（一个数据库×环境一份 `flydb.conf`，密码全部外部注入）、按数据库家族组织脚本仓库、CI 流水线统一命令序列与退出码门禁、存量库 baseline 接入、驱动分发与离线执行机。

参考移植自 Flydb 仓库 `docs/getting-started/multi-environment.md`（对应 CLI 0.2.0）；命令与配置细节由 `flydb-cli-release` 技能提供。

目录：

```text
skills/flydb-multi-environment/
├── SKILL.md
├── references/
│   └── multi-environment.md   # 多数据库多环境自动化组织模式
└── evals/
    └── evals.json
```

本地安装：

```bash
npx skills add . --skill flydb-multi-environment
```

### flydb（技能族总入口）

Flydb 技能族的调度路由器：按用户诉求路由到对应子技能或技能组合，并提供跨技能的端到端组合工作流（从零接入、新迁移需求、多环境发布、失败处置）。路由器保持薄，不复制子技能内容。

技能族服务于开源项目 [Flydb](https://github.com/zzxCoding/Flydb)（zzxCoding/Flydb，Apache-2.0；国内镜像 [Gitee](https://gitee.com/zzhenxuan/Flydb)）——面向任意 JDBC 数据库的 Schema 版本化迁移工具，内置达梦、人大金仓、openGauss、OceanBase、TiDB 等信创数据库方言。开源不易，欢迎 Star 支持与参与贡献。

| 技能 | 职责 |
|---|---|
| `flydb-cli-release` | Java 预检、发行包获取与验证、执行 CLI 命令、驱动接入 |
| `flydb-migration-scripts` | 迁移脚本的新增/修改/组织、命名与版本策略、checksum 纪律 |
| `flydb-multi-environment` | 多环境配置矩阵、密码分层、CI 流水线、baseline、离线执行机 |

目录：

```text
skills/flydb/
├── SKILL.md
└── evals/
    └── evals.json
```

本地安装（技能族一起装，组合使用效果最好；各子技能也可独立安装）：

```bash
npx skills add . --skill flydb
npx skills add . --skill flydb-cli-release
npx skills add . --skill flydb-migration-scripts
npx skills add . --skill flydb-multi-environment
```

## 分发渠道

```bash
# Vercel skills CLI（skills.sh 生态），逐个技能安装
npx skills add https://github.com/zzxCoding/skills --skill flydb

# Claude Code 插件市场（整族安装）
# /plugin marketplace add zzxCoding/skills
# /plugin install flydb-skills@zzxcoding-skills

# 国内备选：腾讯 SkillHub（GitHub 不可达时，提示词安装，见下）
# 请根据 https://skillhub.cn/install/skillhub.md，安装 @user_c9b8aa6a/flydb。
```

- **[skills.sh](https://skills.sh)（Vercel）**：安装遥测自动进榜，无需提交；平台例行安全审计。
- **[ClawHub](https://clawhub.ai)**：经 GitHub Actions 发布（[.github/workflows/clawhub-publish.yml](.github/workflows/clawhub-publish.yml)）。需在仓库 Secrets 配置 `CLAWHUB_TOKEN`；首次经 workflow 发布的技能归入 `other` 分类，需在 ClawHub 设置页补充 categories/topics。
- **腾讯 [SkillHub](https://skillhub.cn)（国内备选渠道）**：GitHub 不可达时的备选安装渠道。flydb 技能族已整套发布（`@user_c9b8aa6a/flydb` 及三个子技能），把提示词复制给 AI 助手即可安装，不经 GitHub；仓库同时保持 topics 与安装命令标注，便于其他聚合平台自动收录。
- **Flydb 国内镜像（Gitee）**：[gitee.com/zzhenxuan/Flydb](https://gitee.com/zzhenxuan/Flydb)，方便国内用户访问 Flydb 源码与文档；CLI 发行包同步发布在 GitHub 与 Gitee Release。

## 设计依据

- 遵循 [Agent Skills 规范](https://agentskills.io/specification)的 `SKILL.md` 与 YAML frontmatter 约定。
- 采用 [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)和 [Anthropic Skills](https://github.com/anthropics/skills)使用的 `skills/<name>/` 集合式目录。
- 把确定性的扫描与写入放在 `scripts/`，让 `SKILL.md` 聚焦工作流和行为边界。
- 把需要随技能离线可用的参考内容打包进 `references/`，技能自包含、复制即用；移植的参考文档标注来源版本，便于上游更新时同步。
