import argparse, os, re, sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

# ---- ROOT 推导 ----
# 优先级：
# 1) --root 显式指定（最高优先）
# 2) 默认向上逐级查找：从脚本目录开始，逐级向上找第一个含 SKILL.md 或 README.md 的目录。
#    兼容发布包布局（scripts/ -> _shared_tools -> 包根）与全局安装布局
#    （~/.codex/skills/_shared_tools/scripts -> ... -> ~/.codex/skills 即 skills 根）。
parser = argparse.ArgumentParser(description="校验 skill 套件的 SKILL.md frontmatter 合规性")
parser.add_argument("--root", help="显式指定扫描根目录（默认向上逐级推导）")
args = parser.parse_args()

if args.root:
    ROOT = os.path.abspath(args.root)
else:
    # 默认向上逐级查找 skills 根：命中条件 = 目录下存在至少一个非 _shared_tools
    # 的子目录含 SKILL.md，或目录自身含 SKILL.md（根级总入口）。
    # 兼容发布包布局（scripts/ -> _shared_tools -> 包根，包根含全部 skill 子目录）
    # 与全局安装布局（~/.codex/skills/_shared_tools/scripts -> ... -> skills 根）。
    # 仅以"含 SKILL.md 子目录"为信号，避免把恰好有 README.md 的用户主目录误判为根。
    d = os.path.dirname(os.path.abspath(__file__))
    ROOT = None
    while True:
        has_sub_skill = any(
            os.path.isdir(os.path.join(d, sub)) and sub != "_shared_tools"
            and os.path.isfile(os.path.join(d, sub, "SKILL.md"))
            for sub in os.listdir(d)
        )
        if has_sub_skill or os.path.isfile(os.path.join(d, "SKILL.md")):
            ROOT = d
            break
        parent = os.path.dirname(d)
        if parent == d:  # 已到文件系统根
            break
        d = parent
    if ROOT is None:
        print("错误: 无法自动定位 skills 根目录（向上未找到含 SKILL.md 子目录的目录）。请用 --root 显式指定。", file=sys.stderr)
        sys.exit(2)

if not os.path.isdir(ROOT):
    print(f"错误: 指定目录不存在: {ROOT}", file=sys.stderr)
    sys.exit(2)

errors, warns, ok = [], [], 0

for d in sorted(os.listdir(ROOT)):
    if d == "_shared_tools" or d.startswith('.') or not os.path.isdir(os.path.join(ROOT, d)):
        continue
    sk = os.path.join(ROOT, d, "SKILL.md")
    if not os.path.isfile(sk):
        sk = os.path.join(ROOT, d, "SKILL.sub.md")
    if not os.path.isfile(sk):
        continue
    with open(sk, encoding="utf-8") as f:
        txt = f.read()
    # frontmatter
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if not m:
        errors.append(f"[{d}] 无合法 frontmatter (--- 包裹)")
        continue
    fm = m.group(1)
    def get(field):
        mm = re.search(rf"^{field}\s*:\s*(.+)$", fm, re.M)
        return mm.group(1).strip() if mm else None
    name = get("name")
    lic  = get("license")
    desc = get("description")
    author = get("skill-author") or re.search(r"skill-author\s*:\s*(.+)", fm)
    author = author.group(1).strip() if hasattr(author,'group') else author
    ver = re.search(r"version\s*:\s*(.+)", fm)
    kws = re.search(r"keywords\s*:", fm)
    trig = re.search(r"triggers\s*:", fm)
    # checks
    if not name:
        errors.append(f"[{d}] 缺 name")
    elif not re.fullmatch(r"[a-z0-9_-]+", name):
        errors.append(f"[{d}] name 含非法字符（仅允许小写字母、数字、连字符或下划线）: {name}")
    elif name != d:
        warns.append(f"[{d}] name({name}) 与目录名不一致")
    if not lic:
        errors.append(f"[{d}] 缺 license")
    elif "Apache" in lic and "MIT" in lic:
        warns.append(f"[{d}] license 同时含 Apache 与 MIT，需明确: {lic}")
    if not desc:
        errors.append(f"[{d}] 缺 description")
    if not author:
        errors.append(f"[{d}] metadata 缺 skill-author")
    if not ver:
        warns.append(f"[{d}] metadata 缺 version")
    if not kws:
        warns.append(f"[{d}] metadata 缺 keywords")
    if not trig:
        warns.append(f"[{d}] metadata 缺 triggers")
    ok += 1

# 根级总入口 SKILL.md（多 skill 套件包在根目录放总入口时校验）
root_sk = os.path.join(ROOT, "SKILL.md")
if os.path.isfile(root_sk):
    with open(root_sk, encoding="utf-8") as f:
        txt = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if not m:
        errors.append("[根SKILL.md] 无合法 frontmatter (--- 包裹)")
    else:
        fm = m.group(1)
        rname = re.search(r"^name\s*:\s*(.+)$", fm, re.M)
        rlic  = re.search(r"^license\s*:\s*(.+)$", fm, re.M)
        rdesc = re.search(r"^description\s*:\s*(.+)$", fm, re.M)
        rau   = re.search(r"skill-author\s*:\s*(.+)", fm)
        rver  = re.search(r"version\s*:\s*(.+)", fm)
        rkws  = re.search(r"keywords\s*:", fm)
        rtrg  = re.search(r"triggers\s*:", fm)
        if not rname: errors.append("[根SKILL.md] 缺 name")
        elif not re.fullmatch(r"[a-z0-9_-]+", rname.group(1).strip()):
            errors.append(f"[根SKILL.md] name 含非法字符: {rname.group(1).strip()}")
        if not rlic: errors.append("[根SKILL.md] 缺 license")
        if not rdesc: errors.append("[根SKILL.md] 缺 description")
        if not rau: warns.append("[根SKILL.md] metadata 缺 skill-author")
        if not rver: warns.append("[根SKILL.md] metadata 缺 version")
        if not rkws: warns.append("[根SKILL.md] metadata 缺 keywords")
        if not rtrg: warns.append("[根SKILL.md] metadata 缺 triggers")
        ok += 1

# 发布包版本一致性：避免 VERSION、根 Skill 和运行文档各自漂移。
version_values = {}
version_file = os.path.join(ROOT, "VERSION")
if os.path.isfile(version_file):
    version_values["VERSION"] = open(version_file, encoding="utf-8").read().strip()
if os.path.isfile(root_sk):
    root_version = re.search(r"^\s+version\s*:\s*([^\r\n]+)$", txt, re.M)
    if root_version:
        version_values["SKILL.md"] = root_version.group(1).strip().strip("\"'")
for doc in ("README.md", "RUN.md"):
    path = os.path.join(ROOT, doc)
    if not os.path.isfile(path):
        continue
    content = open(path, encoding="utf-8").read()
    doc_version = re.search(r"版本[：:]\s*([0-9]+(?:\.[0-9]+)+)", content)
    if doc_version:
        version_values[doc] = doc_version.group(1)
if version_values and len(set(version_values.values())) > 1:
    errors.append("发布版本不一致: " + ", ".join(f"{k}={v}" for k, v in version_values.items()))

print(f"共扫描 SKILL.md: {ok} 个 (扫描根: {ROOT})")
print(f"错误(必须修): {len(errors)}")
for e in errors: print("  [ERROR]", e)
print(f"警告(建议修): {len(warns)}")
for w in warns[:40]: print("  [WARN]", w)
print("结论:", "全部合规 [OK]" if not errors else "存在必须修复项 [ERROR]")

# 扫描数为 0 视为校验失败（杜绝"0 个也全部合规"的假阳性）
if ok == 0:
    print("错误: 扫描到 0 个 SKILL.md，请检查 --root 是否正确（当前扫描根下没有 skill 目录）。", file=sys.stderr)
    sys.exit(1)
sys.exit(1 if errors else 0)
