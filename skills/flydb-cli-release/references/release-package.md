# 发布包：获取、安装与 Java 运行环境

> 本文件随 `flydb-cli-release` 技能打包，对应 Flydb CLI 0.2.1。

## 发布包形态

Flydb CLI 以 GitHub Release ZIP 分发，不依赖安装器，解压即用：

```text
https://github.com/zzxCoding/Flydb/releases/download/v<version>/flydb-cli-<version>.zip
```

例如 `v0.2.0` 对应 `flydb-cli-0.2.1.zip`。解压后得到基目录 `flydb-cli-<version>/`，布局如下：

| 路径 | 内容 |
|---|---|
| `bin/flydb` | POSIX sh 启动器（负责解析 Java 并启动 CLI） |
| `bin/flydb.bat` | Windows 启动器 |
| `lib/` | 全部运行时 JAR |
| `conf/flydb.conf.sample` | 配置模板 |
| `drivers/` | JDBC 驱动目录（附说明；**不捆绑任何 JDBC 驱动**） |
| `docs/` | 与版本匹配的 CLI/配置/错误码文档 |
| `flydb-skills/` | 与版本匹配的 Agent Skills |
| `README.md`、`AGENTS.md`、`LICENSE`、`NOTICE` 等 | 项目说明与许可 |

安装即解压，没有其他步骤；升级等于解压新版本目录并切换引用路径。两个自动化小提示：

- `unzip` 解压到已存在的同名目录时会交互询问覆盖——脚本/自动化场景加 `-o`（如 `unzip -qo`），或先移走旧目录。
- 第 1 步的探测管道（`find ... | grep .` 之类）在无命中时退出码非 0，这是"没找到"而不是命令故障，以实际输出判断，不要一见非零退出码就报错。

## 获取策略（按顺序尝试）

1. **探测已有安装**：先找环境中现成的 `bin/flydb`。候选位置包括 `flydb-cli-*` 解压目录、`/opt/flydb*`、`~/flydb*` 等，可用类似下面的命令探测：
   ```bash
   find ~ /opt /usr/local -maxdepth 4 -type f -name flydb -path '*/bin/flydb' 2>/dev/null
   ```
   找到后运行 `<该目录>/bin/flydb version` 验证可用，直接复用，不重复下载。
2. **复用本地 ZIP**：本机已有发行包（如 `~/Downloads/flydb-cli-*.zip`）时优先解压复用：
   ```bash
   unzip -q ~/Downloads/flydb-cli-0.2.1.zip -d ~/tools/
   ```
3. **按 URL 模式下载**：前两步都没有时，从 GitHub Release 下载。下载是运行时动作；离线或网络不可达时如实报告缺少发行包，不要猜测替代来源或把源码目录当作已安装的 CLI：
   ```bash
   curl -fL -o flydb-cli-0.2.1.zip \
     https://github.com/zzxCoding/Flydb/releases/download/v0.2.1/flydb-cli-0.2.1.zip
   ```

## Java 运行环境（前置条件）

Flydb CLI 是 Java 程序，**要求 Java 8 或更高版本**（JDK 或 JRE 均可）。执行任何 `bin/flydb` 命令前先预检：

```bash
java -version          # 或设置了 JAVA_HOME 时：
"$JAVA_HOME/bin/java" -version
```

注意版本信息输出在 stderr。启动器 `bin/flydb` 的行为：

- **解析顺序**：优先 `$JAVA_HOME/bin/java`；未设置 `JAVA_HOME` 时用 PATH 上的 `java`。
- **版本校验**：自动处理 `1.8` 旧式版本号；主版本低于 8 时拒绝启动。
- **失败表现**（退出码 4，配置错误类）：
  - 未找到 Java：`错误：未找到 Java。请安装 Java 8 或更高版本，或正确设置 JAVA_HOME。`
  - 版本过低：`错误：Flydb 要求 Java 8 或更高版本，当前为 <version>。`
- **JVM 参数**：通过 `FLYDB_JAVA_OPTS` 环境变量按词拆分传入，例如：
  ```bash
  FLYDB_JAVA_OPTS='-Xmx1g -Dfile.encoding=UTF-8' bin/flydb migrate
  ```

Java 缺失或版本过低时：明确报告缺失并停止后续步骤；用户安装任意 JDK 8+ 发行版（如 Temurin、Zulu 或系统包管理器提供的 OpenJDK）并正确设置 `JAVA_HOME` 后重试，不要试图绕过校验。

## 配置文件查找顺序

`--config` 显式指定的文件 → 当前目录 `flydb.conf` → 安装目录 `conf/flydb.conf`。发行包自带的 `conf/flydb.conf.sample` 是配置模板，可复制改名后使用；各配置键含义见 [configuration.md](configuration.md)。

## 验证安装

```bash
bin/flydb version        # 输出 CLI 版本，证明 Java 与发行包均就绪
bin/flydb init --help    # 所有子命令都支持 --help
```

`bin/flydb version` 不连接数据库，是环境预检的最后一步；它成功后才开始涉及数据库的任务。
