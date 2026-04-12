from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BANK_PATH = PROJECT_ROOT / "data" / "public_teaching_bank.json"


def ensure_bank_file() -> None:
    BANK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if BANK_PATH.exists():
        return

    BANK_PATH.write_text(
        json.dumps(
            [
                {
                    "id": "res_math_matrix_001",
                    "title": "矩阵乘法维度检查讲义",
                    "subject": "数学",
                    "resource_type": "lesson_note",
                    "tags": ["矩阵乘法", "维度匹配", "基础规则"],
                    "content": "先判断左矩阵列数是否等于右矩阵行数，再决定能否相乘。可用行列配对图帮助学生理解。",
                    "source": "教师公共题库",
                },
                {
                    "id": "res_math_matrix_002",
                    "title": "矩阵乘法变式题一",
                    "subject": "数学",
                    "resource_type": "exercise",
                    "tags": ["矩阵乘法", "变式题", "计算训练"],
                    "content": "给出两组维度不同的矩阵，让学生先判断是否可乘，再说明原因，最后完成可乘组的运算。",
                    "source": "教师公共题库",
                },
                {
                    "id": "res_math_function_001",
                    "title": "二次函数最值教学卡",
                    "subject": "数学",
                    "resource_type": "lesson_note",
                    "tags": ["二次函数", "最值", "图像法"],
                    "content": "结合抛物线开口方向、顶点坐标和对称轴，用图像法帮助学生理解最值问题。",
                    "source": "教师公共题库",
                },
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_bank() -> list[dict[str, Any]]:
    ensure_bank_file()
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def save_bank(items: list[dict[str, Any]]) -> None:
    ensure_bank_file()
    BANK_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def search_bank(query: str, topic: str = "", limit: int = 3) -> list[dict[str, Any]]:
    items = load_bank()
    tokens = [token.lower() for token in [query, topic] if token]

    if not tokens:
        return items[:limit]

    scored: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        haystack = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("subject", "")),
                " ".join(item.get("tags", [])),
                str(item.get("content", "")),
            ]
        ).lower()
        score = sum(token in haystack for token in tokens)
        if score:
            scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    if scored:
        return [item for _, item in scored[:limit]]
    return items[:limit]
