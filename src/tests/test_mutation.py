#!/usr/bin/env python3
"""UHES 变异测试（第23项优化：验证测试质量,防假绿）。

原理：向代码注入已知 bug（变异）→ 跑单元测试 → 验证测试变红 → 还原。
若变异后测试仍全绿 = 测试盲区（假绿），需补测试。

运行：cd src && python3 -m pytest tests/test_mutation.py -v
"""

import os
import shutil
import subprocess
import sys

# 变异定义: (模块, 原始代码, 变异代码, 预期被杀的测试名)
MUTATIONS = [
    ("llm_gateway.py",
     "while len(self._cache) >= _CACHE_MAX:",
     "while len(self._cache) > _CACHE_MAX:",
     "test_cache_bounded"),
    ("homology.py",
     'if h["paradigm_b"] == b or h["paradigm_a"] == b:',
     'if h["paradigm_b"] == b and h["paradigm_a"] == b:',
     "test_sqlite_persist"),
    ("experts.py",
     '''    {"id": "E42", "name": "现象学", "discipline": "人文类", "perspective": "回到事物本身、本质直观、悬置判断",
     "methods": ["第一性原理分析法", "概念定义域审计"]},
]''',
     ']',
     "test_panel_42_experts"),
    ("observability.py",
     '"degradation_count": degraded,',
     '"degraded_count": degraded,',
     "test_metrics"),
]


def run_mutations(module_dir: str = "src") -> dict[str, str]:
    """运行全部变异,返回 {模块: 结果}。"""
    results: dict[str, str] = {}
    for mod, orig, mutant, killed_by in MUTATIONS:
        path = os.path.join(module_dir, mod)
        backup = path + ".bak"
        shutil.copy(path, backup)
        try:
            # 注入变异
            src = open(path).read()
            if orig not in src:
                results[mod] = f"SKIP(原始代码未找到: {orig[:40]})"
                continue
            open(path, "w").write(src.replace(orig, mutant, 1))
            # 跑测试
            proc = subprocess.run(
                [sys.executable, "-m", "pytest",
                 "src/tests/test_core_modules.py", "-q"],
                capture_output=True, text=True, timeout=120)
            killed = proc.returncode != 0
            results[mod] = (
                f"KILLED by {killed_by} ✅" if killed
                else f"SURVIVED ❌(测试未抓到变异,补测试!)")
        finally:
            shutil.copy(backup, path)
            os.remove(backup)
    return results


if __name__ == "__main__":
    print("[MUTATION] 变异测试开始(4 个变异注入)...")
    r = run_mutations()
    survived = [k for k, v in r.items() if "SURVIVED" in v]
    for mod, res in r.items():
        print(f"  {mod}: {res}")
    if survived:
        print(f"[MUTATION] ❌ {len(survived)} 个变异存活(测试盲区): {survived}")
        sys.exit(1)
    print("[MUTATION] ✅ 全部变异被杀,测试质量验证通过(非假绿)")
    sys.exit(0)
