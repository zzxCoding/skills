# 脚本目录错误码与修改纪律

> 本文件随 `flydb-migration-scripts` 技能打包，对应 Flydb CLI 0.2.1。完整错误码表见姊妹技能 `flydb-cli-release` 的 `references/errors.md`；此处只收录与迁移脚本目录直接相关的部分。

## 修改纪律（红线）

1. **已应用的 `V` 脚本绝不修改**。checksum 记录在历史表 `flydb_schema_history` 中，改动文件内容即触发 `FLYDB-2003`。对已应用版本的任何变更——改 SQL、改格式、改文件名——都用**新版本脚本**承载。
2. **`R` 脚本的修改等于重跑**。这是设计语义而非事故：checksum 变化后下次 migrate 重新执行。修改 R 脚本前确认它幂等/可重建（典型如视图、函数定义）。
3. **`U` 与 `V` 配对维护**。新增带回退需求的 `V` 脚本时同步提供 `U<同版本>__`；修改已应用 V 的回退逻辑属于变更历史，只能通过新版本承载。
4. **不删除已应用的脚本文件**。删掉后历史记录变 `MISSING`（`FLYDB-2003`）。迁移目录切换期间把新旧位置逗号并列：

```properties
flydb.locations=filesystem:/opt/app/new-migrations,filesystem:/opt/flydb/db/migration
```

5. **`repair` 改写历史表**，不属于本技能的日常操作：修正脚本后由用户明确决定是否 repair（执行 CLI 命令属 `flydb-cli-release` 技能范围）。不要用 repair 掩盖集合不完整。

## 错误码速查

| 错误码 | 场景 | Agent 应对 |
|---|---|---|
| `FLYDB-2001` | 版本未以数字开头、含空段/非法字符，或 `V`/`U` 候选命名无法解析；目录版本模式下文件版本不属于目录版本族 | 按命名规则改名（`V<版本>__<描述>.sql`）；不要建议忽略该文件继续 |
| `FLYDB-2002` | 多个脚本解析为同一版本（含 `1` 与 `1.0` 这类语义等价版本） | 为新脚本分配唯一版本号 |
| `FLYDB-2003` | checksum 不一致 / 已应用脚本 `MISSING` / 历史版本 `FUTURE` | 分类处理，见下节 |
| `FLYDB-2004` | 历史表存在 `success=false` 的失败记录 | 修正脚本内容后，由用户决定 repair 清除失败记录，再继续 migrate；不要直接重跑或自动 repair |
| `FLYDB-2005` | 发现旧式 `R<version>__...sql` | 回退脚本改名 `U<version>__...sql`，可重复脚本改名 `R__...sql`；无兼容开关 |
| `FLYDB-2006` | 未启用 `out-of-order` 时出现低版本补执行 | 按序补齐，或与用户确认后设置 `out-of-order=true` |
| `FLYDB-2008` | `undo` 时最近版本没有对应 `U<版本>__` 脚本 | 补齐配对的撤销脚本 |
| `FLYDB-2009` | 未定义占位符，或业务运行时模板被误识别 | 前者补 `flydb.placeholders.*` 或 `-D<key>=<value>`；后者设 `placeholder-replacement=false` 原样保留，不要为模板变量随意赋值 |
| `FLYDB-4005` | `flydb.locations` 指向的目录不存在 | 核对前缀（`filesystem:`/`classpath:`）与路径；相对路径注意 CWD，或改绝对路径 |

## FLYDB-2003 分类处置

`FLYDB-2003` 有三种详情，处理方向完全不同，先看消息里的分类再动手：

- **checksum 不一致**：本地文件内容与历史记录的 checksum 不符。先查明改动是否预期——团队确实修正过脚本内容 → 由用户决定是否 repair 对齐；无人承认改动 → 用版本控制对比找回原文件，不要急于 repair。
- **`MISSING`**：历史表里有记录但当前迁移集合里找不到该脚本。按顺序检查：`locations` 配置是否变了、执行 CLI 的当前工作目录、路径过滤条件（glob/regex 是否把脚本滤掉）、代码版本是否落后。这些都正常才考虑脚本被误删。
- **`FUTURE`**：数据库历史版本比本地脚本新。通常是连错了环境或本地代码没拉到最新；先核对环境与分支，不要在本地"补写"高版本脚本去迎合。

## 失败记录的处置顺序

`migrate` 中途失败会留下 `success=false` 记录，后续 `migrate` 被 `FLYDB-2004` 阻断。正确顺序：

1. 按错误消息定位失败的脚本、语句序号与行号（`FLYDB-2010`）。
2. 修正脚本内容——注意该脚本**尚未成功应用**，修正它不违反修改纪律。
3. 与用户确认后执行 `repair` 清除失败记录（若方言 DDL 非事务，还需评估已执行部分的影响）。
4. 重新 `validate` → `--dry-run migrate` → `migrate`。
