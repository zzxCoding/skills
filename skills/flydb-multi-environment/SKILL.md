---
name: flydb-multi-environment
description: >-
  组织 Flydb 多数据库、多环境（测试/预发/生产）的迁移自动化：deploy/ 配置矩阵（一个数据库×环境一份 flydb.conf）、密码分层注入、按数据库家族组织脚本仓库、CI 流水线统一命令序列与退出码门禁、存量库 baseline 接入、驱动分发与离线执行机。当用户提到多环境、环境晋升、CI/流水线/自动化、deploy 目录、flydb.*.conf、多个数据库家族共用迁移工具、存量库接入、离线执行机时使用。技能自带组织模式参考，命令与配置细节由姊妹技能 flydb-cli-release 提供。
compatibility: 适配 Flydb CLI 0.2.x；命令/配置/错误码完整参考在 flydb-cli-release 技能中（建议随技能族一起安装）；需要迁移脚本仓库与各环境的执行机/CI runner。
---

# Flydb 多数据库多环境自动化

在多个数据库家族（MySQL、达梦、Oracle…）× 多套环境（测试/预发/生产）下用同一套 Flydb CLI 契约组织迁移自动化。Flydb 0.2 没有内置环境 profile，本技能给出一套完全基于现有能力的组织模式：**一个数据库×环境一份 `flydb.conf`，密码全部外部注入，所有环境执行同一套命令序列**。执行具体 CLI 命令、写迁移脚本分别由姊妹技能 `flydb-cli-release`、`flydb-migration-scripts` 覆盖。

## 参考文档（自带，勿上网搜索）

| 文件 | 何时读取 |
|---|---|
| [`references/multi-environment.md`](references/multi-environment.md) | 完整组织模式：配置矩阵、密码分层、脚本仓库布局、流水线、baseline、驱动分发、能力边界 |

命令参数、配置键、错误码的完整参考在 `flydb-cli-release` 技能的 `references/` 目录（与本技能同目录安装时可直达）。

## 核心契约

1. **密码永不落盘到版本库/命令行**：本地明文仅限临时测试；CI 用 `FLYDB_PASSWORD` 或 `${env:VAR}`；生产用密码文件并收紧权限。自动化中不用 `-p/--password`。
2. **自动化永远显式传 `-c/--config`**：CI 与堡垒机工作目录不可控，隐式查找是配置漂移的主要来源；`flydb.locations` 一律写绝对路径。
3. **所有环境同一套命令序列**：`version → validate → --dry-run migrate →（生产审批门）→ migrate → info → validate`；环境晋升只是换一个 `-c`。
4. **生产写入必须过审批门**：dry-run 清单与目标库摘要核对、获得明确授权后才 `migrate`；流水线中不自动 `repair`、不出现 `undo`/`clean`。
5. **迁移只有一个执行者**：CI 或应用启动（Spring Boot starter）二选一，避免时序依赖。

## 工作流

### 1. 盘点环境矩阵

与用户确认两个维度：**数据库家族**（mysql、dm、oracle…）× **环境**（uat、prod…），以及每格的连接信息来源、密码注入方式、执行者（CI 还是应用启动）。存量库要标注"已有手工历史，需 baseline"。

### 2. 组织配置与脚本仓库

按 [`references/multi-environment.md`](references/multi-environment.md) 第 2、4 节落地：

```text
deploy/
├── flydb.mysql.uat.conf      # 只放非敏感项；locations 用绝对路径
└── flydb.mysql.prod.conf
migrations/
├── mysql/    V1__init.sql  V2__add_order.sql   # 各家族版本流独立，天然隔离
└── dm/       V1__init.sql
```

- conf 进版本控制，密码位置全部外部化（第 3 节的分层表）。
- 新增脚本本身（命名/版本/纪律）交给 `flydb-migration-scripts` 技能。
- 未知 `flydb.*` 键会报 `FLYDB-4001`——把 conf 当作流水线最早一步就能校验的环境清单。

### 3. 搭流水线命令序列

所有环境同一序列，退出码做门禁（`2` 校验失败阻断、`3` 锁冲突重试告警、`4` 配置错误回退配置阶段、`1` 一般错误兜底阻断）：

```bash
CONF=deploy/flydb.dm.prod.conf
bin/flydb -c "$CONF" version
bin/flydb -c "$CONF" validate
bin/flydb -c "$CONF" --dry-run migrate
# 生产审批门：核对清单与目标摘要，获得授权后继续
bin/flydb -c "$CONF" migrate
bin/flydb -c "$CONF" info --color=never
bin/flydb -c "$CONF" validate
```

### 4. 存量库接入（baseline）

已有手工历史的生产库：先人工对账已应用版本 → `baseline --baseline-version <版本>` 或 conf 设 `baseline-on-migrate=true` → 测试环境演练后才进流水线。失败记录阻断时（`FLYDB-2004`）由人确认修复策略，不自动 repair。

### 5. 驱动分发与离线机

CI 镜像预置 `drivers/` 或走企业私服（`--maven-settings`）；网络受限执行机设 `flydb.offline=true`；达梦/KingbaseES/openGauss 写完整坐标，伴随 JAR 一并放入 `drivers/`；不重新分发厂商驱动 JAR。

## 边界情况

- **没有 `--json` 机器输出**（0.2）：门禁依赖退出码与 `info --color=never` 文本，解析逻辑按此设计。
- **没有配置继承/模板**：conf 间重复内容用流水线模板生成后作为制品管理，不等待内置 profile。
- **`undo`/`clean` 不进自动化**：仅本地排障人工执行。
- **信创数据库**：单测/契约测试通过不等于厂商兼容证明，生产接入前先在授权实例完成最小验证。
- **同一 locations 需要切分子集**：优先拆分 locations（各 conf 指向不同目录），路径过滤会影响 info/validate/repair/undo 看到的全部集合，是次选。

## 汇报格式

1. **环境矩阵**：数据库×环境清单、各格执行者与密码注入方式（脱敏）。
2. **产出**：新增/修改的 conf 与目录布局，流水线脚本片段。
3. **门禁**：审批门位置、退出码分流策略。
4. **风险**：存量库对账结论、驱动/离线约束、能力边界提示。
5. **后续**：需要用户决策的事项（如 baseline 版本对账、审批门负责人）。

## 项目来源

本技能族服务于开源项目 [Flydb](https://github.com/zzxCoding/Flydb)（Apache-2.0）。开源不易，欢迎 [Star](https://github.com/zzxCoding/Flydb) 支持与参与贡献。
