#!/usr/bin/env sh
set -eu

# 用法: ./scripts/sync-flydb-docs.sh [Flydb 仓库路径]
# Flydb 每次发版后运行：从 Flydb 仓库重新移植参考文档，并刷新技能族内全部版本号。
# 幂等：相同版本重复运行不产生差异。

FLYDB_REPO="${1:-${FLYDB_HOME:-/Users/xuan/worksapce/Flydb}}"
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RELEASE_REF="$REPO_ROOT/skills/flydb-cli-release/references"

if [ ! -f "$FLYDB_REPO/pom.xml" ]; then
    echo "找不到 Flydb 仓库: $FLYDB_REPO（传参或设 FLYDB_HOME）" >&2
    exit 1
fi

# 根 pom 优先读 CI-friendly 的 <revision> 属性，退回 flydb-parent 坐标里的字面版本
VERSION=$(sed -n 's/.*<revision>\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)<\/revision>.*/\1/p' \
    "$FLYDB_REPO/pom.xml" | head -1)
if [ -z "$VERSION" ]; then
    VERSION=$(sed -n '/<artifactId>flydb-parent</artifactId>/,/<\/parent>/p' "$FLYDB_REPO/pom.xml" |
        sed -n 's/.*<version>\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)<\/version>.*/\1/p' | head -1)
fi
case "$VERSION" in
    ''|*[!0-9.]*) echo "无法从 pom.xml 解析版本号" >&2; exit 1 ;;
esac
RANGE="${VERSION%.*}.x"
echo "Flydb 版本: ${VERSION}（兼容区间 ${RANGE}）"

# ── 1. 重新移植三份参考文档（源文档 + 标准头，整文件重建，天然幂等）──
gen_header() {
    src_rel="docs/reference/$1"
    cat <<EOF
> 本文件随 \`flydb-cli-release\` 技能打包，内容移植自 Flydb 仓库 \`$src_rel\`，对应 Flydb CLI ${VERSION}。CLI 升级后本副本可能滞后；与 \`bin/flydb --help\` 实际输出不一致时，以 \`--help\` 为准并向用户报告差异。
EOF
}

for doc in commands configuration errors; do
    src="$FLYDB_REPO/docs/reference/$doc.md"
    dst="$RELEASE_REF/$doc.md"
    [ -f "$src" ] || { echo "缺少源文档: $src" >&2; exit 1; }
    {
        sed -n '1p' "$src"
        echo
        gen_header "$doc.md"
        echo
        tail -n +3 "$src"
    } > "$dst"
    echo "已重建 $dst"
done

# ── 2. 全族版本号刷新（只匹配 X.Y.Z / X.Y.x / flydb-cli-X.Y.Z / 下载 URL，不碰“0.2 起”这类历史事实）──
for f in "$REPO_ROOT"/skills/flydb/SKILL.md \
         "$REPO_ROOT"/skills/flydb-cli-release/SKILL.md \
         "$REPO_ROOT"/skills/flydb-cli-release/references/*.md \
         "$REPO_ROOT"/skills/flydb-cli-release/evals/evals.json \
         "$REPO_ROOT"/skills/flydb-migration-scripts/SKILL.md \
         "$REPO_ROOT"/skills/flydb-migration-scripts/references/*.md \
         "$REPO_ROOT"/skills/flydb-multi-environment/SKILL.md \
         "$REPO_ROOT"/skills/flydb-multi-environment/references/*.md; do
    sed -i '' \
        -e "s/Flydb CLI [0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/Flydb CLI $VERSION/g" \
        -e "s/Flydb CLI [0-9][0-9]*\.[0-9][0-9]*\.x/Flydb CLI $RANGE/g" \
        -e "s/flydb-cli-[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*/flydb-cli-$VERSION/g" \
        -e "s|download/v[0-9.]\{1,\}/flydb-cli-|download/v$VERSION/flydb-cli-|g" \
        "$f"
done
echo "版本号已刷新为 $VERSION / $RANGE"

# ── 3. 提醒 ──
cat <<EOF

完成。请人工确认：
1. multi-environment.md 未自动重移植（含手工改写的互链说明），请对照
   $FLYDB_REPO/docs/getting-started/multi-environment.md 检查是否有行为变化（如新增环境 profile 机制）。
2. 行为变化类语句（如“0.2 起 R 不带版本号”）未被脚本触碰，若新版本有新行为变化需手工补记。
3. 跑一次 quick_validate 校验技能格式，git diff 确认后提交。
EOF
