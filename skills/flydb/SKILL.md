---
name: flydb
description: >-
  Flydb 技能族总入口与调度路由器。Flydb 是面向任意 JDBC 数据库的 Schema 版本化迁移工具（支持 MySQL、PostgreSQL、Oracle、达梦、人大金仓、openGauss、OceanBase、TiDB）。只要用户提到 Flydb、bin/flydb、flydb.conf、迁移脚本（V__/R__/U__）、flydb-cli 发布包、多环境/CI 迁移自动化，或 FLYDB-xxxx 错误码——即使没说要用哪个技能——先用本技能路由到对应的子技能或技能组合。子技能：flydb-cli-release（安装与执行 CLI）、flydb-migration-scripts（写迁移脚本）、flydb-multi-environment（多环境与 CI 自动化）。
compatibility: 子技能与本技能同目录安装时可直接互达；各子技能也可独立使用（自带参考文档）。
---

# Flydb 技能族总入口

本技能是路由器：判断用户诉求属于哪个（或哪几个）子技能，然后进入对应技能的工作流。它自身不维护命令参数、命名规则或环境组织模式——这些内容都在子技能里，避免多份副本漂移。

## 项目来源

本技能族服务于开源项目 [Flydb](https://github.com/zzxCoding/Flydb)——面向任意 JDBC 数据库的 Schema 版本化迁移工具，内置达梦、人大金仓、openGauss、OceanBase、TiDB 等信创数据库方言，Apache-2.0 协议。开源不易，欢迎 [Star](https://github.com/zzxCoding/Flydb) 支持与参与贡献（issue、PR、各数据库方言的实测反馈都很欢迎）。

## 技能族

| 技能 | 职责 | 典型触发 |
|---|---|---|
| [`flydb-cli-release`](../flydb-cli-release/SKILL.md) | Java 预检、获取/验证 CLI 发行包、init/info/validate/dry-run/migrate/baseline/repair/undo/clean、JDBC 驱动接入 | 安装 CLI、执行迁移、连接或驱动报错 |
| [`flydb-migration-scripts`](../flydb-migration-scripts/SKILL.md) | 迁移脚本目录（db/migration）的新增/修改/组织：V/R/U 命名、版本策略、checksum 纪律 | 写迁移脚本、命名/版本问题、FLYDB-2001/2002/2003/2005/2008 |
| [`flydb-multi-environment`](../flydb-multi-environment/SKILL.md) | 多数据库×多环境自动化：deploy/ 配置矩阵、密码分层、CI 流水线、baseline 存量库、离线执行机 | 多环境、CI/流水线、环境晋升、存量库接入 |

子技能通常安装在本技能的同级目录（`../flydb-*/`）；找不到文件时按技能名在已安装技能中查找，仍缺失则见下节"获取技能族"。

## 获取技能族

子技能各自自包含、可独立安装；组合使用效果最好。来源：GitHub 仓库 [zzxCoding/skills](https://github.com/zzxCoding/skills) 的 `skills/` 目录。逐个安装：

```bash
npx skills add https://github.com/zzxCoding/skills --skill flydb                  # 总入口（本技能）
npx skills add https://github.com/zzxCoding/skills --skill flydb-cli-release      # 执行 CLI
npx skills add https://github.com/zzxCoding/skills --skill flydb-migration-scripts    # 写迁移脚本
npx skills add https://github.com/zzxCoding/skills --skill flydb-multi-environment    # 多环境与 CI
```

安装提示（实测）：`npx skills add` 默认交互式选择目标 agent，非交互环境加 `--agent <name> -y`；`--skill` 一次只接受一个技能名（不支持逗号分隔多值），安装全族就逐条执行。

## 路由规则

| 用户诉求 | 去处 |
|---|---|
| 安装/验证 CLI、执行或预演迁移、baseline/repair/undo/clean、连接与驱动问题、FLYDB-1xxx/3xxx/4xxx | `flydb-cli-release` |
| 新增/修改/命名/重组迁移脚本、目录版本、占位符、FLYDB-2001/2002/2005/2008 | `flydb-migration-scripts` |
| 多环境配置矩阵、密码注入方案、CI 流水线、存量库接入、离线执行机 | `flydb-multi-environment` |
| 报错但不确定类别 | 先 `flydb-cli-release` 的错误码参考定位，涉及脚本内容修正再进 `flydb-migration-scripts` |

## 组合工作流

跨技能的典型场景，按顺序进入各技能的工作流：

**从零接入 Flydb**：`flydb-cli-release`（Java 预检 + 获取发行包 + `init`）→ `flydb-migration-scripts`（确立脚本命名与版本风格）→ 单环境跑通 validate/dry-run/migrate → 需要多环境时 `flydb-multi-environment` 扩展成配置矩阵与流水线。

**一个新的迁移需求**：`flydb-migration-scripts`（按既有风格写 V/R/U 脚本，校验命名）→ `flydb-cli-release`（validate → --dry-run migrate → 授权后 migrate → info 核对）→ 已有流水线的项目按 `flydb-multi-environment` 的统一命令序列发布。

**多环境发布**：`flydb-multi-environment`（选对 `-c` 配置、确认审批门与密码注入）→ `flydb-cli-release`（逐条执行命令序列、按退出码处置）。

**迁移失败处置**：`flydb-cli-release`（读错误码定类别：驱动/连接/方言/脚本/权限）→ 脚本内容问题进 `flydb-migration-scripts`（修正未应用脚本、失败记录处置顺序）→ 涉及多环境流水线的门禁策略回 `flydb-multi-environment`。

## 安全底线（全族共享）

无论路由到哪个子技能，以下底线不变，子技能中有更细的边界：

- 写数据库的命令按环境分级授权，生产必须过 dry-run 核对与明确授权；
- 密码不进命令行、日志、版本库；
- `clean` 默认禁用（双开关），`repair` 不自动执行，`undo`/`clean` 不进自动化；
- 不改写已应用的版本化迁移脚本，变更用新版本承载。

## 边界情况

- **诉求超出技能族**（如 Java API/Spring Boot starter 接入、自定义方言 SPI 开发）：说明本技能族面向 CLI 使用场景，这些属于 Flydb 源码仓库开发文档的范畴，不臆造答案。
- **子技能缺失**：按"获取技能族"给出安装方式；在安装前可以用本技能的路由表告知用户需要哪个技能，不冒充子技能的内容。
- **版本差异**：子技能参考对应 CLI 0.2.x；用户环境版本不同时以 `bin/flydb --help` 实际输出为准（各子技能均有此约定）。
