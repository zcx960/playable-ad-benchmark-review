#!/usr/bin/env python3
"""Validate a playable-ad benchmark feedback report using standard library only."""

import argparse
import json
import re
import sys
from pathlib import Path


def validate(text):
    errors = []
    warnings = []
    checks = {
        "竞品对比": "竞品" in text,
        "证据范围": "证据范围" in text or "实测范围" in text,
        "具体修改": text.count("具体修改") >= 3,
        "验收标准": text.count("验收标准") >= 3,
        "P0 优先级": "P0" in text,
        "P1 优先级": "P1" in text,
        "P2 优先级": "P2" in text,
        "数值口径": "数值口径" in text or "建议值" in text,
    }
    labels = {
        "竞品对比": "缺少竞品对照内容",
        "证据范围": "缺少证据范围或实测范围说明",
        "具体修改": "至少需要 3 处明确的‘具体修改’小节",
        "验收标准": "至少需要 3 处明确的‘验收标准’小节",
        "P0 优先级": "缺少 P0 优先级",
        "P1 优先级": "缺少 P1 优先级",
        "P2 优先级": "缺少 P2 优先级",
        "数值口径": "缺少竞品实测值/建议值等数值口径说明",
    }
    for key, ok in checks.items():
        if not ok:
            errors.append(labels[key])

    number_count = len(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?(?:\s*[—–-]\s*\d+(?:\.\d+)?)?", text))
    if number_count < 8:
        errors.append("可量化信息不足：次数、时长、尺寸、容量或节奏基准少于 8 处")

    vague = re.compile(r"提升质感|优化体验|加强反馈|更加丝滑|增强打击感|提升高级感|更有质感")
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if vague.search(line):
            if not re.search(r"\d", line) and not any(x in line for x in ("不得", "不能只写", "不合格")):
                warnings.append(f"第 {number} 行含模糊表述且缺少量化细节：{line[:100]}")
        if len(line) > 350:
            warnings.append(f"第 {number} 行段落过长（{len(line)} 字符），建议拆分以便制作执行")

    if len(text.strip()) < 1200:
        warnings.append("正文较短，请确认是否覆盖视觉、首次操作、核心循环、奖励与验收")

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "characters": len(text),
            "specific_change_sections": text.count("具体修改"),
            "acceptance_sections": text.count("验收标准"),
            "quantified_values": number_count,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="检查可玩广告对比反馈是否具体、完整、可验收")
    parser.add_argument("report", type=Path, help="Markdown 反馈报告路径")
    args = parser.parse_args()
    try:
        text = args.report.read_text(encoding="utf-8")
    except Exception as exc:
        print(json.dumps({"passed": False, "errors": [f"无法读取报告：{exc}"], "warnings": []}, ensure_ascii=False, indent=2))
        return 2
    result = validate(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
