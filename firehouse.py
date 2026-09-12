#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
firehouse.py —— FireHouse 记录脚本
用法:
  python firehouse.py <AI名> "<本轮干了什么>"          # 用文本直接记录
  python firehouse.py <AI名> --file <路径.md>          # 用现成 md 文件记录
  python firehouse.py <AI名> --interactive            # 交互式输入

行为: 生成时间戳文件(自动按 FORMAT.md 模板) -> git add -> git commit。
一条命令, 一层土。
"""
import argparse
import datetime
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))

def safe_name(name: str) -> str:
    """目录名清洗: 只留字母数字中文和 _-"""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\-]", "", name)
    return cleaned or "AI"

def ts_now():
    return datetime.datetime.now()

def write_record(ai: str, body: str) -> str:
    d = safe_name(ai)
    ai_dir = os.path.join(REPO, d)
    os.makedirs(ai_dir, exist_ok=True)
    now = ts_now()
    fname = now.strftime("%Y-%m-%d_%H%M") + ".md"
    path = os.path.join(ai_dir, fname)
    # 关键词 = 正文第一行截断
    first = next((l.strip() for l in body.splitlines() if l.strip()), "记录")
    keyword = re.sub(r"[#\s]", "", first)[:16] or "记录"
    fname2 = now.strftime("%Y-%m-%d_%H%M") + "_" + keyword + ".md"
    path = os.path.join(ai_dir, fname2)
    lines = [
        "# " + first[:60],
        "",
        "- AI：" + d,
        "- 时间：" + now.strftime("%Y-%m-%d %H:%M"),
        "",
        "## 本轮干了什么",
        "",
        body.strip(),
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path

def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("git " + " ".join(args) + " 失败:", r.stderr.strip()[:300], file=sys.stderr)
    return r

def main():
    ap = argparse.ArgumentParser(description="FireHouse 记录脚本")
    ap.add_argument("ai", help="AI 名字（对应一层目录）")
    ap.add_argument("content", nargs="?", default=None, help="本轮干了什么（一句话也行）")
    ap.add_argument("--file", default=None, help="用现成 md 文件作为记录内容")
    ap.add_argument("--interactive", action="store_true", help="交互式输入")
    args = ap.parse_args()

    if args.interactive:
        print("请输入记录内容（最后一行空行结束）:")
        buf = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip() and buf:
                break
            buf.append(line)
        body = "\n".join(buf).strip()
        if not body:
            print("空记录，放弃。", file=sys.stderr)
            sys.exit(1)
    elif args.file:
        if not os.path.isfile(args.file):
            print("文件不存在:", args.file, file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            body = f.read().strip()
    else:
        body = (args.content or "").strip()
        if not body:
            print("没内容。用法: python firehouse.py <AI名> \"<内容>\"", file=sys.stderr)
            sys.exit(1)

    path = write_record(args.ai, body)
    print("写入:", path)

    # 落土 = add + commit
    git("add", "-A")
    r = git("commit", "-m", os.path.basename(path).replace(".md", ""))
    if r.returncode == 0:
        print("commit 成功: 这层土落定了。")
    else:
        print("commit 未生成（可能是无变化），土还在原地。", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
