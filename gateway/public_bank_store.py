from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gateway.governance import compute_copyright_risk


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BANK_PATH = PROJECT_ROOT / "data" / "public_teaching_bank.json"


def _default_items() -> list[dict[str, Any]]:
    return [
        {
            "id": "res_math_matrix_001",
            "title": "矩阵乘法维度检查讲义",
            "subject": "数学",
            "resource_type": "lesson_note",
            "tags": ["矩阵乘法", "维度匹配", "基础规则"],
            "content": "先判断左矩阵列数是否等于右矩阵行数，再决定能否相乘。可用行列配对图帮助学生理解。",
            "source": "教师公共题库",
            "owner_teacher": "李四",
            "copyright_level": "school_authorized",
            "access_scope": "school",
            "allow_fulltext_to_student": False,
            "allow_derivative_generation": True,
        },
        {
            "id": "res_math_matrix_002",
            "title": "矩阵乘法变式题一",
            "subject": "数学",
            "resource_type": "exercise",
            "tags": ["矩阵乘法", "变式题", "计算训练"],
            "content": "给出两组维度不同的矩阵，让学生先判断是否可乘，再说明原因，最后完成可乘组的运算。",
            "source": "教师公共题库",
            "owner_teacher": "李四",
            "copyright_level": "class_authorized",
            "access_scope": "class",
            "allow_fulltext_to_student": False,
            "allow_derivative_generation": True,
        },
        {
            "id": "res_math_function_001",
            "title": "二次函数最值教学卡",
            "subject": "数学",
            "resource_type": "lesson_note",
            "tags": ["二次函数", "最值", "图像法"],
            "content": "结合抛物线开口方向、顶点坐标和对称轴，用图像法帮助学生理解最值问题。",
            "source": "教师公共题库",
            "owner_teacher": "李四",
            "copyright_level": "public_open",
            "access_scope": "public",
            "allow_fulltext_to_student": True,
            "allow_derivative_generation": True,
        },
    ]


def ensure_bank_file() -> None:
    BANK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if BANK_PATH.exists():
        return
    BANK_PATH.write_text(json.dumps(_default_items(), ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(item)
    normalized.setdefault("source", "教师公共题库")
    normalized.setdefault("owner_teacher", "李四")
    normalized.setdefault("copyright_level", "school_authorized")
    normalized.setdefault("access_scope", "school")
    normalized.setdefault("allow_fulltext_to_student", False)
    normalized.setdefault("allow_derivative_generation", True)
    normalized.setdefault("tags", [])
    return normalized


def load_bank() -> list[dict[str, Any]]:
    ensure_bank_file()
    items = json.loads(BANK_PATH.read_text(encoding="utf-8-sig"))
    normalized_items = [_normalize_item(item) for item in items]
    if normalized_items != items:
        save_bank(normalized_items)
    return normalized_items


def save_bank(items: list[dict[str, Any]]) -> None:
    ensure_bank_file()
    BANK_PATH.write_text(
        json.dumps([_normalize_item(item) for item in items], ensure_ascii=False, indent=2),
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
                str(item.get("copyright_level", "")),
                str(item.get("access_scope", "")),
            ]
        ).lower()
        score = sum(token in haystack for token in tokens)
        if score:
            scored.append((score, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    if scored:
        return [item for _, item in scored[:limit]]
    return items[:limit]


def summarize_content(text: str, max_length: int = 80) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 1] + "…"


def evaluate_student_access(
    item: dict[str, Any],
    requester_role: str = "student",
    propagation_depth: int = 2,
    iteration_count: int = 1,
) -> dict[str, Any]:
    copyright_level = item.get("copyright_level", "school_authorized")
    access_scope = item.get("access_scope", "school")
    allow_fulltext = bool(item.get("allow_fulltext_to_student", False))
    allow_derivative = bool(item.get("allow_derivative_generation", True))
    content = str(item.get("content", "")).strip()

    preferred_mode = "fulltext" if allow_fulltext else "substitute_generation" if allow_derivative else "summary"
    copyright_risk = compute_copyright_risk(
        resource=item,
        requester_role=requester_role,
        propagation_depth=propagation_depth,
        exposure_mode=preferred_mode,
        iteration_count=iteration_count,
    )

    if allow_fulltext and copyright_level == "public_open" and copyright_risk["policy"] == "allow":
        return {
            "decision": "fulltext",
            "reason": "公开资源允许学生直接查看原文。",
            "student_visible_content": content,
            "teacher_policy_hint": "学生可直接查看全文",
            "copyright_risk": copyright_risk,
        }

    if (
        allow_fulltext
        and access_scope in {"public", "school", "class"}
        and copyright_level != "teacher_private"
        and copyright_risk["policy"] == "allow"
    ):
        return {
            "decision": "fulltext",
            "reason": "资源已授权学生查看原文。",
            "student_visible_content": content,
            "teacher_policy_hint": "已授权学生查看全文",
            "copyright_risk": copyright_risk,
        }

    if allow_derivative and copyright_risk["policy"] in {"allow", "summary_or_substitute", "block_or_substitute"}:
        return {
            "decision": "substitute_generation",
            "reason": "不直接开放原文，允许基于知识点生成替代讲解或变式题。",
            "student_visible_content": (
                f"知识点摘要：{summarize_content(content, 72)}\n"
                "AG4 仅向 AG3 提供摘要与变式方向，不回传原始全文。"
            ),
            "teacher_policy_hint": "仅允许摘要与替代生成",
            "copyright_risk": copyright_risk,
        }

    return {
        "decision": "summary_only",
        "reason": "版权限制较强，仅允许输出最小必要摘要。",
        "student_visible_content": f"授权摘要：{summarize_content(content, 56)}",
        "teacher_policy_hint": "仅允许授权摘要",
        "copyright_risk": copyright_risk,
    }


def search_bank_for_student(query: str, topic: str = "", limit: int = 3) -> list[dict[str, Any]]:
    results = search_bank(query=query, topic=topic, limit=limit)
    enriched: list[dict[str, Any]] = []
    for item in results:
        policy = evaluate_student_access(item)
        enriched.append({**item, "delivery_policy": policy})
    return enriched
