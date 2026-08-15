---
name: flydb-cli-release
description: >-
  使用 Flydb CLI 发布包完成数据库迁移：Java 环境预检、获取与验证发行包（GitHub Release ZIP）、init、info、validate、--dry-run migrate、migrate、baseline、repair、undo、clean 与 JDBC 驱动接入。当用户提到 Flydb、bin/flydb、flydb-cli-*.zip、flydb.conf、flydb Schema 迁移、JDBC 驱动、--database-type，或要在 MySQL/PostgreSQL/Oracle/达梦/人大金仓/openGauss/OceanBase/TiDB 上跑迁移时使用。技能自带全部命令、配置与错误码参考（references/ 目录），无需查阅外部文档。
compatibility: Flydb CLI 0.2.x；Java 8 或更高版本；需要 flydb-cli 发行包（GitHub Release ZIP 或本地已有安装）与目标数据库的 JDBC 驱动。
---

# Flydb CLI 发布包使用

使用 Flydb 独立 CLI 发行包完成一次可追溯的数据库迁移操作。本技能自包含：命令、配置、错误码参考全部打包在 `references/` 内，复制到任何目录都可独立工作，不依赖 GitHub 文档链接或 Flydb 源码仓库。

本技能属于 Flydb 技能族（总入口为 `flydb` 技能）：写迁移脚本用 `flydb-migration-scripts`，多环境/CI 自动化用 `flydb-multi-environment`。

## 参考文档（自带，勿上网搜索）

| 文件 | 何时读取 |
|---|---|
| [`references/release-package.md`](references/release-package.md) | 获取/安装发行包、Java 运行环境、配置文件查找顺序 |
| [`references/commands.md`](references/commands.md) | 选择子命令、核对全局选项与参数语义 |
| [`references/configuration.md`](references/configuration.md) | 配置键、环境变量、优先级、版本选择/路径过滤规则 |
| [`references/errors.md`](references/errors.md) | 按错误码（FLYDB-xxxx）与退出码分类处理失败 |
| [`references/drivers.md`](references/drivers.md) | JDBC 驱动解析顺序、厂商驱动接入、FLYDB-1003 排查 |

## 核心契约

1. **自包含**：只使用本技能 `references/` 内的文档回答命令与配置问题；除"下载发布包 ZIP"这一运行时动作外，不访问 GitHub 或其他外部文档。
2. **版本基准**：参考对应 CLI 0.2.x。当参考内容与 `bin/flydb --help` 实际输出不一致时，以 `--help` 为准执行，并向用户报告差异。
3. **写入需授权**：`migrate`、`baseline`、`repair`、`undo`、`clean` 都会改变数据库。本地/测试库在用户明确要求后执行；预发/生产库先展示 dry-run 结果与目标摘要，得到明确的写入授权后再执行。目标环境不明时停在只读检查。
4. **密码纪律**：优先 `FLYDB_PASSWORD` 环境变量、`${env:VAR}` 引用或密码文件；不把密码写进命令历史、日志、SQL 或最终汇报；输出中的 JDBC URL 一律脱敏。

## 工作流

### 1. 环境预检与获取发布包

先确认 Java，再确认 CLI，缺一即停：

```bash
java -version                       # 要求 ≥8；版本输出在 stderr
<发行包目录>/bin/flydb version      # 不连数据库，验证发行包与 Java 均就绪
```

发行包按三步获取（详见 [`references/release-package.md`](references/release-package.md)）：

1. 探测已有安装：`find ~ /opt /usr/local -maxdepth 4 -type f -name flydb -path '*/bin/flydb'`
2. 复用本地 ZIP（如 `~/Downloads/flydb-cli-*.zip`），`unzip` 解压
3. 按 URL 模式 `https://github.com/zzxCoding/Flydb/releases/download/v<version>/flydb-cli-<version>.zip` 下载

Java 缺失时报告并停止（安装任意 JDK 8+ 并设置 `JAVA_HOME` 后重试）；发行包缺失且无法下载时如实报告，不要把源码目录当成已安装的 CLI。

### 2. 建立执行上下文

执行任何数据库命令前，明确并在回复中记录：

- 使用的 CLI 路径或发行包目录；
- `flydb.conf` 或 `--config` 来源；
- JDBC URL 的脱敏摘要、目标数据库与方言标识；
- 迁移脚本位置（通常是 `filesystem:db/migration`；脚本在外部仓库时记录解析后的绝对位置和当前工作目录）；
- 这是本地、测试、预发还是生产数据库；
- 用户要查看、校验、预演还是实际写入。

首次接入可用 `init` 生成 `flydb.conf` 与迁移目录（非交互加 `--yes`；已有文件冲突会报 `FLYDB-4004`，不要删除覆盖绕过）。

### 3. 选择命令

| 用户目标 | 命令 | 默认动作 |
|---|---|---|
| 创建配置和迁移目录 | `init` | 只生成本地文件，不连接数据库 |
| 查看迁移状态 | `info` | 读取数据库和本地脚本，不持锁 |
| 校验 checksum、失败记录和迁移集合 | `validate` | 只读校验 |
| 预演迁移 | `--dry-run migrate` | 解析并打印 SQL，不执行 |
| 执行待迁移脚本 | `migrate` | 写入数据库并持锁 |
| 为存量库写入基线 | `baseline` | 写历史记录并持锁 |
| 清理失败记录或对齐 checksum | `repair` | 修改历史表并持锁 |
| 撤销最近一次版本化迁移 | `undo`（支持 `--dry-run`） | 执行 SQL 并持锁 |
| 清空目标 schema | `clean` | 高风险破坏性操作，默认禁用 |

选定命令后到 [`references/commands.md`](references/commands.md) 核对参数；不确定时用 `bin/flydb <命令> --help`。

### 4. 执行

**只读任务**（`info`、`validate`、`version`）：执行后报告退出码和关键结果；不要把只读任务自行扩展为写库命令。

**迁移任务**：

1. 先 `validate`，尽早暴露 checksum、失败记录、非法命名、未定义占位符。
2. 再 `--dry-run migrate`，核对目标方言、待执行脚本、SQL 数量与顺序；任何未解释的缺失或多出脚本都应阻断实际写入。
3. 按核心契约第 3 条取得授权后执行 `migrate`。
4. 执行后用 `info --color=never` 与 `validate` 核对状态，报告是否产生失败记录。

迁移失败时先读 [`references/errors.md`](references/errors.md) 的错误码和数据库原始错误，判断是驱动/连接、方言、脚本还是权限问题。不要自动 `repair`——它会修改历史表，必须在用户确认修复策略后执行。

### 5. 驱动与错误处理

- 驱动相关（`FLYDB-1003`）按 [`references/drivers.md`](references/drivers.md) 的解析轨迹排查。
- 连接失败（`FLYDB-1001`）先查 URL、账号、密码、网络与数据库状态，不要先改方言。
- 探测歧义（`FLYDB-1002`）显式 `--database-type`，不要把未识别数据库强标为 `mysql`/`oracle`。

## 边界情况

- **参考与实际不符**：以 `bin/flydb --help` 为准执行，并向用户报告差异（参考副本可能滞后于已安装的 CLI 版本）。
- **clean**：默认禁用。除非用户明确要求并完成目标确认，不得追加 `--clean-disabled=false --force`（`FLYDB-4003` 是防呆，不是故障）。
- **业务模板占位符**：`${workDate}` 等要原样入库的运行时模板报 `FLYDB-2009` 时，用 `--placeholder-replacement=false`，不要为模板变量随意赋值。
- **迁移目录切换**：新旧位置逗号并列，避免已应用记录变 `MISSING`（`FLYDB-2003`）。
- **不下载、提交或重新分发厂商 JDBC 驱动**；遵守厂商许可证与企业制品库规则。

## 汇报格式

完成后用简洁结构汇报：

1. **目标**：脱敏后的 CLI 路径、数据库/方言、环境和命令。
2. **动作**：实际执行的命令，是否包含 dry-run，是否写入数据库。
3. **结果**：退出码、预期与实际迁移集合核对、迁移数量/状态、失败记录或锁结果。
4. **验证**：`info`、`validate` 或 dry-run 分别验证了什么。
5. **后续**：只给与当前失败或用户目标直接相关的下一步。

## 项目来源

本技能族服务于开源项目 [Flydb](https://github.com/zzxCoding/Flydb)（Apache-2.0）。开源不易，欢迎 [Star](https://github.com/zzxCoding/Flydb) 支持与参与贡献。
