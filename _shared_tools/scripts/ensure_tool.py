"""ensure_tool.py — 开源工具「先检测、再自动安装」通用模块（QueryStrategist 共享）

为什么需要它（踩坑固化）：
  - 部分运行环境注入了未启动的本地代理（HTTP_PROXY/HTTPS_PROXY 指向本地端口），
    pip 若走该代理会 Connection refused 而静默失败 -> 前序第三方库安装卡死的根因之一。
  - 部分运行时 `python -m venv` 的写入被 sandbox 回滚 -> 不能依赖 venv。
  => 本模块：① 先检测工具是否已存在；② 未安装则走国内镜像 + **禁用代理** 直接联网安装；
     ③ 安装到隔离目录（--target，无需 venv），并回传 site_dir 供调用方加入 sys.path。

用法（命令行，供 skill 通过 Bash 调用）：
  python ensure_tool.py --name requests --pip-spec "requests" \
      --import requests
  # 可用 --target 指定隔离目录（默认 ~/.workbuddy/tools/site）；--mirror 覆盖镜像源
  # 输出一行 JSON：{"status":"already_installed|installed|failed", ...}

用法（作为模块，供其它 Python 脚本 import）：
  from ensure_tool import ensure_tool
  res = ensure_tool("requests", pip_spec="requests", import_name="requests")
  if res["status"] in ("already_installed","installed"):
      site_dir = res.get("site_dir")
      # 将 site_dir 加入 sys.path 后即可 import requests
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

# 国内镜像（按顺序回退）：清华 -> 阿里云 -> 官方
DEFAULT_MIRRORS = [
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.org/simple",
]

# 安装超时（毫秒）—— 大依赖树（如 openpyxl / requests 全量）可能较慢
INSTALL_TIMEOUT_MS = 300000


def _default_site_dir():
    # 动态解析，绝不硬编码私人绝对路径；隔离目录，不污染系统环境
    base = os.path.join(os.path.expanduser("~"), ".workbuddy", "tools", "site")
    return base


def _detect(import_name, command, site_dir):
    """检测工具是否可用：能 import 或命令存在即视为已安装。"""
    if import_name:
        cand = [import_name]
        # 部分包 import 名与分发名不同（如包名含连字符时，import 名用下划线）
        if import_name != import_name.lower():
            cand.append(import_name.lower())
        for mod in cand:
            probe = (
                f"import sys;"
                f"sys.path.insert(0, {site_dir!r});"
                f"import {mod}; print('ok')"
            )
            try:
                r = subprocess.run([sys.executable, "-c", probe],
                                   capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    return True
            except Exception:
                pass
    if command:
        in_path = shutil.which(command)
        if in_path:
            return True
        # 检查 target/bin 或 target/Scripts 下的可执行
        if site_dir:
            for sub in ("bin", "Scripts"):
                p = os.path.join(site_dir, sub, command)
                if os.path.isfile(p) or os.path.isfile(p + ".exe"):
                    return True
    return False


def _clean_env():
    """关键：拷贝当前环境并**移除代理变量**，让 pip 直连镜像，绕开死代理。"""
    env = dict(os.environ)
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
              "ALL_PROXY", "all_proxy"):
        env.pop(k, None)
    env["NO_PROXY"] = "*"
    env["PIP_NO_INPUT"] = "1"
    return env


def _install(pip_spec, python, mirror, target, user, env):
    cmd = [python, "-m", "pip", "install", pip_spec,
           "-i", mirror, "--progress-bar", "on",
           "--disable-pip-version-check", "--no-input", "--timeout", "30", "--retries", "2"]
    if target:
        cmd += ["--target", target]
    elif user:
        cmd += ["--user"]
    # 注意：不管道到 tail/head，保证进度条实时可见
    r = subprocess.run(cmd, env=env, timeout=INSTALL_TIMEOUT_MS / 1000)
    return r.returncode == 0


def ensure_tool(name, pip_spec=None, import_name=None, command=None,
                target=None, mirrors=None, python=None, user=False):
    """检测并在缺失时安装一个开源工具。

    返回 dict: status / site_dir / mirror / error 等。
    """
    pip_spec = pip_spec or name
    import_name = import_name or name
    python = python or sys.executable
    site_dir = target or _default_site_dir()
    os.makedirs(site_dir, exist_ok=True)
    mirrors = list(dict.fromkeys(mirrors or DEFAULT_MIRRORS))

    if _detect(import_name, command, site_dir):
        return {"status": "already_installed", "name": name,
                "site_dir": site_dir, "import": import_name}

    env = _clean_env()
    last_err = None
    for m in mirrors:
        try:
            ok = _install(pip_spec, python, m, site_dir, user, env)
        except subprocess.TimeoutExpired as e:
            last_err = f"pip 安装超时（mirror={m}）：{e}"
            continue
        except Exception as e:  # noqa: BLE001
            last_err = f"pip 安装异常（mirror={m}）：{e}"
            continue
        if ok and _detect(import_name, command, site_dir):
            return {"status": "installed", "name": name, "mirror": m,
                    "site_dir": site_dir, "import": import_name}
        last_err = f"pip 退出非零（mirror={m}）"

    # 全部镜像失败 -> 尝试 --user 兜底（仍禁用代理）
    if not user:
        try:
            for m in mirrors:
                ok = _install(pip_spec, python, m, None, True, env)
                if ok and _detect(import_name, command, site_dir):
                    return {"status": "installed", "name": name, "mirror": m,
                            "site_dir": site_dir, "import": import_name,
                            "note": "installed with --user"}
        except Exception as e:  # noqa: BLE001
            last_err = f"--user 兜底也失败：{e}"
    return {"status": "failed", "name": name, "import": import_name,
            "site_dir": site_dir, "error": last_err}


def main():
    ap = argparse.ArgumentParser(description="开源工具检测/自动安装通用模块")
    ap.add_argument("--name", required=True, help="工具显示名")
    ap.add_argument("--pip-spec", help="pip 安装规格（默认同 name）")
    ap.add_argument("--import", dest="import_name", help="Python import 名")
    ap.add_argument("--command", help="命令行可执行名（安装 CLI 工具时使用）")
    ap.add_argument("--target", help="隔离安装目录（默认 ~/.workbuddy/tools/site）")
    ap.add_argument("--mirror", action="append", help="追加镜像源（可多次）")
    ap.add_argument("--python", help="Python 解释器（默认 sys.executable）")
    ap.add_argument("--user", action="store_true", help="用 --user 安装兜底")
    args = ap.parse_args()
    mirrors = DEFAULT_MIRRORS + (args.mirror or [])
    res = ensure_tool(args.name, pip_spec=args.pip_spec,
                      import_name=args.import_name, command=args.command,
                      target=args.target, mirrors=mirrors,
                      python=args.python, user=args.user)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
