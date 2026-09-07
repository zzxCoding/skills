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

使用 [Flydb](https://github.com/zzxCoding/Flydb) CLI 发布包完成数据库迁移：Java 预检、发行包获取与校验、CLI 执行、本机 Web 工作台、JSON/Plan、MCP、长迁移与失败现场处置，以及 JDBC 驱动接入。

技能自带运行所需参考，按 CLI 0.3.x 维护（Web 入口需 0.3.5+）。先核验目标发行包版本，优先读取其匹配文档，再使用技能副本；源码快照不代表公开 Release 已发布。普通 CLI/Web 需要 Java 8+，MCP 宿主另需 Node.js 20+。

目录：

```text
skills/flydb-cli-release/
├── SKILL.md
├── references/
│   ├── commands.md          # CLI 命令参考（移植自 Flydb docs）
│   ├── configuration.md     # 配置项参考（移植自 Flydb docs）
│   ├── errors.md            # 错误码/退出码参考（移植自 Flydb docs）
│   ├── release-package.md   # 发布包获取、校验与 Java 环境
│   ├── drivers.md           # 驱动排障摘要
│   ├── jdbc-integration.md  # 厂商数据库、驱动与方言接入
│   ├── json-output.md       # protocolVersion=1 机器信封
│   ├── plan-artifact.md     # flydb-plan-v1 摘要与边界
│   ├── mcp-tools.md         # 工具白名单、授权与超时
│   ├── web.md               # 原文件管理、预览与进度
│   ├── web-api.md           # 本机 API、确认引用、Run/SSE
│   └── upstream-sync.json   # 来源版本、提交、哈希与适配记录
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

参考依据 Flydb 多环境指南和 CLI 0.3.x 契约维护，使用 JSON/Plan 留档、真实 CI 审批门与失败即停的分阶段示例；命令与配置细节由 `flydb-cli-release` 提供。Web 配置分组不等于配置继承，MCP 写入开关不等于逐次授权。

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
| `flydb-cli-release` | 发行包、CLI/Web/MCP、JSON/Plan、长迁移与失败诊断、驱动接入 |
| `flydb-migration-scripts` | V/R/U 脚本、版本族与过滤、checksum、部分执行后的修复纪律 |
| `flydb-multi-environment` | 配置矩阵、密码注入、JSON/Plan 审批材料、baseline、离线执行机 |

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

## 同步 Flydb 源项目

从本地 Flydb Git checkout 同步 9 份运行参考，并保存输入哈希与源码版本；默认使用相邻的 `../Flydb`，也可传路径或设置 `FLYDB_HOME`。只使用 Python 3 标准库，兼容 macOS/Linux：

```bash
sh scripts/sync-flydb-docs.sh /path/to/Flydb
sh scripts/sync-flydb-docs.sh --check /path/to/Flydb
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
```

`--check` 不写文件：一致返回 0，存在漂移返回 1，输入缺失或无效返回 2。同步先检查全部输入，再写变化文件；重复运行不改内容。技能内互链转为本地引用，未打包的扩展阅读保留固定提交的来源链接。

维护分工：

- **自动同步**：commands、configuration、errors、JSON、Plan、MCP、Web、Web API、JDBC 指南；必要的文档适配记录在 [upstream-sync.json](skills/flydb-cli-release/references/upstream-sync.json)。
- **人工合并**：对比上游 `flydb-cli/SKILL.md` 和多环境指南，更新四个技能的入口、手写参考及 `evals/evals.json`。上游也可能保留旧说法，按当前命令/接口契约核对；同步脚本不会宣称这些工作流已自动审阅。
- **验证**：运行同步脚本测试、四个技能的 `quick_validate.py`、本地引用检查和 `git diff --check`。评测 JSON 是行为场景，格式校验不等于行为评测通过。

同步仅修改当前仓库，不修改 Flydb 源项目、用户已安装的技能目录，也不执行数据库操作或发布。

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
