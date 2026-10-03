#!/usr/bin/env python3
"""专家独立人格测试（真实化清单第4步）。

锁契约：
- 42 位专家全部有独立 persona（style/focus）
- mock 降级输出差异化（不同专家不同观点）
- prompt 模板正确注入 persona
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experts import EXPERTS, PERSONAS, EXPERT_PROMPT_TEMPLATE, ExpertPanel  # noqa: E402


class TestExpertPersona(unittest.TestCase):
    def test_all_experts_have_persona(self):
        """42 位专家全部有独立 persona。"""
        missing = [e["id"] for e in EXPERTS if e["id"] not in PERSONAS]
        self.assertEqual(missing, [])
        self.assertEqual(len(PERSONAS), 42)

    def test_persona_has_style_and_focus(self):
        """每套 persona 有 style 和 focus 字段。"""
        for eid, p in PERSONAS.items():
            self.assertIn("style", p, f"{eid} 缺 style")
            self.assertIn("focus", p, f"{eid} 缺 focus")
            self.assertTrue(p["style"], f"{eid} style 为空")
            self.assertTrue(p["focus"], f"{eid} focus 为空")

    def test_mock_output_differentiated(self):
        """mock 降级：不同专家输出不同（不再趋同）。"""
        panel = ExpertPanel()
        subset = panel.select_subset(["信息论", "语言学", "科研范式", "复杂系统"])
        outs = [panel._mock_deliberate(e, "测试设计") for e in subset]
        # 4 位专家的 strengths 应互不相同（人格差异化）
        strength_sets = {o["strengths"][0] for o in outs}
        self.assertEqual(len(strength_sets), 4, "mock 输出未差异化")

    def test_prompt_injects_persona(self):
        """prompt 模板注入 style/focus。"""
        e16 = next(e for e in EXPERTS if e["id"] == "E16")
        p = PERSONAS["E16"]
        prompt = EXPERT_PROMPT_TEMPLATE.format(
            discipline=e16["discipline"], name=e16["name"],
            style=p["style"], focus=p["focus"],
            requirement="测试需求", paradigm_hints="信息论",
            design_summary="测试设计")
        self.assertIn(p["style"], prompt)
        self.assertIn(p["focus"], prompt)

    def test_select_subset_still_works(self):
        """子集筛选不受 persona 影响。"""
        panel = ExpertPanel()
        subset = panel.select_subset(["信息论", "语言学"])
        names = [e["name"] for e in subset]
        self.assertIn("信息论", names)
        self.assertIn("语言学", names)


if __name__ == "__main__":
    unittest.main()
