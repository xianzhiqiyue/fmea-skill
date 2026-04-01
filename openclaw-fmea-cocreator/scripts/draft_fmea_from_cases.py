from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from retrieve_cases import (
    ALIASES,
    DATA_ROOT,
    RELATED_MODULES,
    Match,
    collect_matches,
    row_text,
    tokenize,
)


SKILL_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SKILL_DIR.parent
ALLOWED_THEMES = {"dfmea_sample_data", "knowledge_base_template"}

FIELD_ALIASES = {
    "analysis_object": ["零件名称", "子系统/功能模块", "子系统/组件", "子系统/部件", "模块", "关联项目/产品"],
    "function": [
        "功能要求",
        "功能描述",
        "标准化功能项",
        "产品寿命周期应用任务和环境剖面",
        "策划和控制内容",
    ],
    "failure_mode": ["潜在失效模式", "失效模式 (AI分类)"],
    "effect": [
        "潜在失效后果 (客户/后工序)",
        "潜在失效后果（客户/后工序）",
        "失效的潜在后果（对客户或后工序的影响）",
        "失效后果 (S)",
    ],
    "severity": ["严重度 (S)", "S"],
    "cause": ["潜在失效起因/机理", "潜在失效原因（机理）", "潜在失效原因", "根本原因分析 (Cause)"],
    "occurrence": ["发生频次 (O)", "O"],
    "current_controls": [
        "现行设计控制 (预防/探测)",
        "现行控制措施",
        "现行控制方法",
        "现行设计/过程控制措施",
        "现行控制措施",
    ],
    "detection": ["可探测度 (D)", "D"],
    "rpn": ["RPN", "初始 RPN"],
    "recommended_actions": [
        "建议改进措施 (控制/预防)",
        "建议的控制措施 (改进方案)",
        "建议措施",
        "建议的预防/探测措施",
    ],
    "post_action_severity": ["措施后 S", "改进后 S", "新S"],
    "post_action_occurrence": ["措施后 O", "改进后 O", "新O"],
    "post_action_detection": ["措施后 D", "改进后 D", "新D"],
    "post_action_rpn": ["措施后 RPN", "改进后 RPN", "新RPN"],
    "owner": ["责任人", "负责人"],
    "target_date": ["计划完成时间", "结束时间"],
}

STOPWORDS = {
    "客户",
    "后工序",
    "系统",
    "功能",
    "要求",
    "建议",
    "设计",
    "控制",
    "改进",
    "方案",
    "模块",
    "项目",
    "产品",
    "组件",
    "部分",
    "过程",
    "进行",
    "用于",
    "增加",
    "导致",
    "无法",
    "工作",
    "模式",
    "分析",
    "输出",
    "表格",
}

SCOPE_PROFILES: dict[str, list[dict[str, Any]]] = {
    "变温系统": [
        {
            "name": "压缩机制冷子系统",
            "keywords": ["压缩机", "冷媒", "气液分离器", "蒸发器", "毛细管", "高压", "继电器", "422", "VX3244", "1028", "启动", "时序"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "液氮蒸发子系统",
            "keywords": ["液氮罐", "主体组件", "排气管组件", "波纹管", "真空", "PTFE", "特氟龙", "换热盘管", "加热棒", "PT100", "航插", "麦拉膜", "G10"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "自动进样器": [
        {
            "name": "运动与抓取子系统",
            "keywords": ["气缸", "滑块", "夹爪", "储样筒", "进样筒", "转盘", "样品管", "扭簧", "导轨", "定位销"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "检测与气路控制子系统",
            "keywords": ["检测", "光电", "传感器", "对射", "气路", "电磁阀", "减压阀", "缓冲气", "压力开关", "气压", "供电", "接口"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "调谐单元": [
        {
            "name": "射频调谐与匹配子系统",
            "keywords": ["射频", "调谐", "匹配", "电容", "打火", "线圈", "焊接", "磁化率", "梯度线圈"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "机械传动与限位子系统",
            "keywords": ["电机", "编码器", "限位", "离合器", "连杆", "齿轮", "减速机", "扭矩"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "EMC与算法控制子系统",
            "keywords": ["EMC", "CAN", "RS422", "MCU", "光耦", "搜索", "陷波", "扫掠", "算法"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "收发机": [
        {
            "name": "发射链路子系统",
            "keywords": ["发射", "上变频", "调幅", "功放驱动", "衰减", "功率", "泄漏"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "接收与采集子系统",
            "keywords": ["接收", "LNA", "ADC", "时钟", "噪声", "解调", "增益"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "频率合成与连接子系统",
            "keywords": ["混频", "本振", "频率合成", "背板", "连接器", "同轴", "杂散"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "前置放大器": [
        {
            "name": "T/R与保护子系统",
            "keywords": ["T/R", "PIN", "高功率", "保护", "限幅", "功率检测", "联动跳闸", "VSWR", "驻波", "复位", "热管理"],
            "min_hits": 2,
            "max_terms": 12,
        },
        {
            "name": "低噪声放大与接口子系统",
            "keywords": ["LNA", "增益", "振荡", "N-K", "BNC", "接口", "回波损耗"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "控制逻辑与供电子系统",
            "keywords": ["UNWORK", "OBSERVE", "Watchdog", "DB-37", "供电", "串扰", "模式切换"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "射频功放": [
        {
            "name": "异常保护与联锁子系统",
            "keywords": ["保护", "联锁", "比较器", "切断", "驻波", "反射功率", "异常检测"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "放大与通道切换子系统",
            "keywords": ["放大", "增益", "双通道", "切换", "热切换", "继电器", "功率管"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "热管理与复位子系统",
            "keywords": ["热管理", "温度", "风扇", "热斑", "复位", "Auto-Recovery", "散热"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "进样筒": [
        {
            "name": "结构与磁兼容子系统",
            "keywords": ["磁性", "无磁", "结构件", "清洗", "磁导率", "铁屑"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "气动与升降子系统",
            "keywords": ["气动", "气源", "缓冲气罐", "软着陆", "升降", "卡阻", "内壁"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "旋转与控制子系统",
            "keywords": ["转子", "旋转", "50Hz", "PID", "光电传感器", "气流阀门"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "匀场单元": [
        {
            "name": "匀场线圈结构子系统",
            "keywords": ["匀场线圈", "几何形状", "固化", "环氧", "真空灌封", "节点松动"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "恒流驱动与连接子系统",
            "keywords": ["SDB", "恒流", "DAC", "基准电压", "DB50", "连接", "检流电阻"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "软件与耦合管理子系统",
            "keywords": ["算法", "通信", "EEPROM", "Watchdog", "互感", "低温匀场", "室温匀场"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
    "电子学机柜": [
        {
            "name": "电源与接地屏蔽子系统",
            "keywords": ["PDU", "电源", "接地", "屏蔽", "导电", "EMC", "胶条"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "结构与门板安全子系统",
            "keywords": ["横梁", "机柜", "前门", "后下门", "后上门", "钢丝绳", "铰链"],
            "min_hits": 2,
            "max_terms": 10,
        },
        {
            "name": "风道与热设计子系统",
            "keywords": ["风道", "过滤棉", "进风", "排风", "热短路", "CFD", "温升"],
            "min_hits": 2,
            "max_terms": 10,
        },
    ],
}


@dataclass
class ScopeDefinition:
    name: str
    query_terms: list[str]
    extracted_terms: list[str] = field(default_factory=list)
    auto_suggested: bool = False
    hit_count: int = 0
    reason: str = ""


@dataclass
class DraftRow:
    scope: str
    analysis_object: str
    function: str
    failure_mode: str
    effect: str
    severity: str
    cause: str
    occurrence: str
    current_controls: str
    detection: str
    rpn: str
    recommended_actions: str
    owner: str
    target_date: str
    confirmation_status: str
    rating_basis: str
    reference_type: str
    source_cases: list[str]
    review_comment: str = ""
    max_match_score: int = 0
    max_scope_hits: int = 0
    confirmation_reasons: list[str] = field(default_factory=list)
    reviewer_focus: str = ""
    boundary_scopes: list[str] = field(default_factory=list)


@dataclass
class ConfirmationItem:
    scope: str
    row_key: str
    why_confirmation_is_needed: str
    suggested_reviewer_focus: str
    reference_type: str
    source_cases: list[str]
    review_comment: str = ""


def load_input_text(args: argparse.Namespace) -> str:
    if args.input_file:
        return Path(args.input_file).read_text(encoding="utf-8").strip()
    if args.input_text:
        return args.input_text.strip()
    raise ValueError("Provide either --input-file or --input-text.")


def valid_token(token: str) -> bool:
    token = token.strip()
    if not token or token in STOPWORDS:
        return False
    if len(token) < 2 or len(token) > 24:
        return False
    if re.fullmatch(r"[\d\-.:%]+", token):
        return False
    if token.lower() in {"rpn", "excel", "json", "csv"}:
        return False
    return True


def build_lexicon() -> list[str]:
    counts: Counter[str] = Counter()
    for json_file in sorted(DATA_ROOT.glob("*/json/*.json")):
        payload = json.loads(json_file.read_text(encoding="utf-8"))
        if payload.get("theme") not in ALLOWED_THEMES:
            continue
        for row in payload.get("filled_rows", []):
            text = row_text(row)
            if not text:
                continue
            for token in tokenize(text):
                if valid_token(token):
                    counts[token] += 1
    ranked = sorted(counts.items(), key=lambda item: (-len(item[0]), -item[1], item[0]))
    return [token for token, _ in ranked]


def extract_query_terms(input_text: str, module: str | None, limit: int = 16) -> list[str]:
    lexicon = build_lexicon()
    found: list[str] = []
    for token in lexicon:
        if token in input_text and token not in found:
            found.append(token)
        if len(found) >= limit:
            break
    if module:
        if module not in found:
            found.insert(0, module)
        for canonical, alias_list in ALIASES.items():
            if module == canonical or module in alias_list:
                for item in [canonical, *alias_list]:
                    if item not in found:
                        found.append(item)
    return found


def parse_scope(raw_scope: str) -> ScopeDefinition:
    if "::" not in raw_scope:
        raise ValueError(f"Invalid --scope value: {raw_scope}. Use 'Scope Name::keyword1 keyword2'.")
    name, raw_terms = raw_scope.split("::", 1)
    terms = [term for term in tokenize(raw_terms) if valid_token(term)]
    if not name.strip() or not terms:
        raise ValueError(f"Invalid --scope value: {raw_scope}.")
    return ScopeDefinition(name=name.strip(), query_terms=terms, auto_suggested=False, reason="manual")


def canonicalize_module(module: str) -> str:
    if module in SCOPE_PROFILES:
        return module
    for canonical, aliases in ALIASES.items():
        if module == canonical or module in aliases:
            return canonical
    return module


def module_family_rank(sheet: str, module: str | None) -> int:
    canonical_module = canonicalize_module(module) if module else None
    if not canonical_module:
        return 0

    same_names = {canonical_module, *ALIASES.get(canonical_module, [])}
    if sheet in same_names:
        return 2

    related_modules = RELATED_MODULES.get(canonical_module, [])
    related_names = {name for related in related_modules for name in [related, *ALIASES.get(related, [])]}
    if sheet in related_names:
        return 1

    return 0


def suggest_scopes(module: str, input_text: str, extracted_terms: list[str]) -> list[ScopeDefinition]:
    canonical_module = canonicalize_module(module)
    profiles = SCOPE_PROFILES.get(canonical_module, [])
    lowered = input_text.lower()
    suggestions: list[ScopeDefinition] = []

    for profile in profiles:
        keywords = profile["keywords"]
        hit_keywords = [keyword for keyword in keywords if keyword.lower() in lowered]
        if len(hit_keywords) < profile["min_hits"]:
            continue

        query_terms: list[str] = []
        for keyword in hit_keywords:
            if keyword not in query_terms:
                query_terms.append(keyword)
        for term in extracted_terms:
            if term in keywords and term not in query_terms:
                query_terms.append(term)
        for keyword in keywords:
            if keyword not in query_terms:
                query_terms.append(keyword)
            if len(query_terms) >= profile["max_terms"]:
                break

        suggestions.append(
            ScopeDefinition(
                name=profile["name"],
                query_terms=query_terms[: profile["max_terms"]],
                extracted_terms=[term for term in extracted_terms if term in query_terms],
                auto_suggested=True,
                hit_count=len(hit_keywords),
                reason=f"matched keywords: {' / '.join(hit_keywords[:8])}",
            )
        )

    suggestions.sort(key=lambda scope: (-scope.hit_count, scope.name))
    return suggestions


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def read_match_row(match: Match, cache: dict[Path, Any]) -> dict[str, str]:
    json_path = PROJECT_ROOT / match.source
    if json_path not in cache:
        cache[json_path] = json.loads(json_path.read_text(encoding="utf-8"))
    payload = cache[json_path]
    for row in payload.get("filled_rows", []):
        if row.get("__excel_row__") == match.excel_row:
            return row
    raise KeyError(f"Could not find row {match.excel_row} in {json_path}")


def first_value(row: dict[str, str], field_name: str) -> str:
    for key in FIELD_ALIASES[field_name]:
        value = normalize_space(row.get(key, ""))
        if value:
            return value
    return ""


def safe_int(value: str) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def compute_rpn(severity: str, occurrence: str, detection: str, current_rpn: str) -> str:
    if current_rpn:
        return current_rpn
    s_value = safe_int(severity)
    o_value = safe_int(occurrence)
    d_value = safe_int(detection)
    if s_value is None or o_value is None or d_value is None:
        return ""
    return str(s_value * o_value * d_value)


def combine_unique(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        cleaned = normalize_space(value)
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return "\n".join(seen)


def dedupe_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        first_value(row, "analysis_object"),
        first_value(row, "function"),
        first_value(row, "failure_mode"),
        first_value(row, "effect"),
    )


def scope_hit_count(row: dict[str, str], scope_terms: list[str]) -> int:
    primary_text = " ".join(
        [
            first_value(row, "analysis_object"),
            first_value(row, "function"),
            first_value(row, "failure_mode"),
            first_value(row, "effect"),
            first_value(row, "cause"),
        ]
    )
    lowered = primary_text.lower()
    return sum(1 for term in scope_terms if term.lower() in lowered)


def scope_focus_score(row: dict[str, str], scope_terms: list[str]) -> int:
    focus_text = " ".join(
        [
            first_value(row, "analysis_object"),
            first_value(row, "function"),
            first_value(row, "failure_mode"),
        ]
    ).lower()
    context_text = " ".join(
        [
            first_value(row, "effect"),
            first_value(row, "cause"),
        ]
    ).lower()
    score = 0
    for term in scope_terms:
        lowered = term.lower()
        if lowered in focus_text:
            score += 2
        elif lowered in context_text:
            score += 1
    return score


def best_scope_name(row: dict[str, str], scopes: list[ScopeDefinition]) -> str | None:
    ranked = []
    for index, scope in enumerate(scopes):
        ranked.append(
            (
                scope_focus_score(row, scope.query_terms),
                scope_hit_count(row, scope.query_terms),
                -index,
                scope.name,
            )
        )
    best = max(ranked)
    if best[0] <= 0 and best[1] <= 0:
        return None
    return best[3]


def boundary_scope_names(row: dict[str, str], current_scope: str, scopes: list[ScopeDefinition]) -> list[str]:
    current_focus = 0
    current_hits = 0
    candidates: list[tuple[int, int, str]] = []

    for scope in scopes:
        focus = scope_focus_score(row, scope.query_terms)
        hits = scope_hit_count(row, scope.query_terms)
        if scope.name == current_scope:
            current_focus = focus
            current_hits = hits
        if focus > 0 or hits > 0:
            candidates.append((focus, hits, scope.name))

    boundaries: list[str] = []
    for focus, hits, scope_name in candidates:
        if scope_name == current_scope:
            continue
        if current_focus > 0:
            if focus >= current_focus - 1 and hits > 0:
                boundaries.append(scope_name)
        elif current_hits > 0 and hits >= current_hits:
            boundaries.append(scope_name)

    return boundaries


def build_reference_type(matches_for_row: list[Match], module: str | None) -> str:
    family_ranks = [module_family_rank(match.sheet, module) for match in matches_for_row]
    if any(rank >= 2 for rank in family_ranks):
        return "current module"
    if any(rank == 1 for rank in family_ranks):
        return "direct family reference"
    return "broader analogy"


def build_confirmation_reasons(
    reference_type: str,
    boundary_scopes: list[str],
    themes: set[str],
    severity: str,
    occurrence: str,
    detection: str,
) -> list[str]:
    reasons: list[str] = []
    missing_scores = [label for label, value in [("S", severity), ("O", occurrence), ("D", detection)] if not value]
    if missing_scores:
        reasons.append(f"源案例缺少完整评分字段：{'/'.join(missing_scores)}")
    elif not occurrence or not detection:
        reasons.append("O/D 评分依据仍不完整")

    if reference_type != "current module":
        reasons.append("该行主要来自跨模块家族类比，需要确认是否适用于当前模块责任范围")

    if boundary_scopes:
        reasons.append(f"scope 归属存在边界，当前放在本 scope，但也可能属于：{' / '.join(boundary_scopes)}")

    if any(theme != "dfmea_sample_data" for theme in themes):
        reasons.append("来源中包含模板或知识库条目，需要确认是否已落到具体机理和现行控制")

    return reasons


def build_confirmation_status(reasons: list[str]) -> str:
    if reasons:
        return "needs expert confirmation"
    return "draft"


def build_rating_basis(
    themes: set[str],
    reference_type: str,
    severity: str,
    occurrence: str,
    detection: str,
) -> str:
    parts: list[str] = []

    if severity:
        parts.append(f"S={severity} 继承自历史案例的后果强度")
    else:
        parts.append("S 未在源案例中明确给出")

    if occurrence and detection:
        if themes == {"dfmea_sample_data"}:
            parts.append(f"O={occurrence}、D={detection} 继承自成品 DFMEA，但仍需结合本企业标尺校准")
        else:
            parts.append(f"O={occurrence}、D={detection} 来自混合来源，需结合真实试验与控制能力校准")
    else:
        parts.append("O/D 未完整继承，需专家补齐评分依据")

    if reference_type != "current module":
        parts.append(f"本行属于 {reference_type}，仅建议作为补缺参考")

    return "；".join(parts)


def build_reviewer_focus(reference_type: str, boundary_scopes: list[str], occurrence: str, detection: str) -> str:
    focus_points: list[str] = []
    if boundary_scopes:
        focus_points.append("确认 scope 归属与责任边界")
    if reference_type != "current module":
        focus_points.append("确认该类比是否适用于当前模块机理、接口和责任范围")
    if not occurrence or not detection:
        focus_points.append("补齐 O/D 与现行检测控制")
    else:
        focus_points.append("校准 O/D 与实际保护、测试和筛选能力是否匹配")
    return "；".join(focus_points)


def row_key(row: DraftRow) -> str:
    head = normalize_space(row.analysis_object or row.function or row.scope or "未命名对象")
    tail = normalize_space(row.failure_mode or "待补失效模式")
    return f"{head} / {tail}"


def short_text(value: str, limit: int = 80) -> str:
    text = normalize_space(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def first_action_candidate(actions: str) -> str:
    for line in actions.splitlines():
        cleaned = normalize_space(line)
        if cleaned:
            return short_text(cleaned, limit=80)
    return ""


def build_confirmation_queue(scope_rows: dict[str, list[DraftRow]]) -> list[ConfirmationItem]:
    items: list[ConfirmationItem] = []
    for rows in scope_rows.values():
        for row in rows:
            if row.confirmation_status != "needs expert confirmation":
                continue
            items.append(
                ConfirmationItem(
                    scope=row.scope,
                    row_key=row_key(row),
                    why_confirmation_is_needed="；".join(row.confirmation_reasons),
                    suggested_reviewer_focus=row.reviewer_focus,
                    reference_type=row.reference_type,
                    source_cases=row.source_cases,
                    review_comment=row.review_comment,
                )
            )
    return items


def build_top_risks(scope_rows: dict[str, list[DraftRow]]) -> list[dict[str, str]]:
    rows = sorted(
        [row for rows in scope_rows.values() for row in rows if safe_int(row.rpn) is not None],
        key=lambda item: (-(safe_int(item.rpn) or 0), -item.max_match_score),
    )[:8]
    return [
        {
            "scope": row.scope,
            "row_key": row_key(row),
            "failure_mode": row.failure_mode,
            "current_rpn": row.rpn,
            "why_it_matters": short_text(row.effect, 100),
            "first_action_candidate": first_action_candidate(row.recommended_actions),
            "reference_type": row.reference_type,
        }
        for row in rows
    ]


def build_suggested_actions(scope_rows: dict[str, list[DraftRow]]) -> list[dict[str, str]]:
    rows = [
        row
        for rows in scope_rows.values()
        for row in rows
        if normalize_space(row.recommended_actions)
    ]
    rows.sort(
        key=lambda item: (
            -(safe_int(item.rpn) or -1),
            item.reference_type != "current module",
            -item.max_match_score,
            row_key(item),
        )
    )
    return [
        {
            "scope": row.scope,
            "row_key": row_key(row),
            "current_rpn": row.rpn,
            "recommended_action": row.recommended_actions,
            "owner": row.owner,
            "target_date": row.target_date,
            "confirmation_status": row.confirmation_status,
            "review_comment": row.review_comment,
            "reference_type": row.reference_type,
            "source_case": "; ".join(row.source_cases),
        }
        for row in rows
    ]


def build_source_trace(scope_rows: dict[str, list[DraftRow]]) -> list[dict[str, Any]]:
    return [
        {
            "scope": row.scope,
            "row_key": row_key(row),
            "reference_type": row.reference_type,
            "source_cases": row.source_cases,
        }
        for rows in scope_rows.values()
        for row in rows
    ]


def aggregate_rows(scope: ScopeDefinition, scopes: list[ScopeDefinition], matches: list[Match], module: str | None) -> list[DraftRow]:
    cache: dict[Path, Any] = {}
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    relevant_rows: list[tuple[Match, dict[str, str], int, int]] = []

    for match in matches:
        row = read_match_row(match, cache)
        hits = scope_hit_count(row, scope.query_terms)
        if hits <= 0:
            continue
        focus_score = scope_focus_score(row, scope.query_terms)
        relevant_rows.append((match, row, module_family_rank(match.sheet, module), focus_score))

    restrict_to_family = sum(1 for _, _, family_rank, _ in relevant_rows if family_rank > 0) >= 4

    for match, row, family_rank, focus_score in relevant_rows:
        if restrict_to_family and family_rank <= 0:
            continue
        if family_rank == 1 and focus_score < 2:
            continue
        if family_rank <= 0 and focus_score < 2:
            continue
        if best_scope_name(row, scopes) != scope.name:
            continue
        key = dedupe_key(row)
        if not any(key):
            continue
        entry = grouped.setdefault(
            key,
            {
                "rows": [],
                "matches": [],
            },
        )
        entry["rows"].append(row)
        entry["matches"].append(match)

    draft_rows: list[DraftRow] = []
    for _, bundle in grouped.items():
        rows = bundle["rows"]
        matches_for_row: list[Match] = bundle["matches"]
        analysis_object = combine_unique([first_value(row, "analysis_object") for row in rows])
        function = combine_unique([first_value(row, "function") for row in rows])
        failure_mode = combine_unique([first_value(row, "failure_mode") for row in rows])
        effect = combine_unique([first_value(row, "effect") for row in rows])
        severity = next((value for value in [first_value(row, "severity") for row in rows] if value), "")
        cause = combine_unique([first_value(row, "cause") for row in rows])
        occurrence = next((value for value in [first_value(row, "occurrence") for row in rows] if value), "")
        current_controls = combine_unique([first_value(row, "current_controls") for row in rows])
        detection = next((value for value in [first_value(row, "detection") for row in rows] if value), "")
        rpn = compute_rpn(
            severity,
            occurrence,
            detection,
            next((value for value in [first_value(row, "rpn") for row in rows] if value), ""),
        )
        recommended_actions = combine_unique([first_value(row, "recommended_actions") for row in rows])
        owner = combine_unique([first_value(row, "owner") for row in rows])
        target_date = combine_unique([first_value(row, "target_date") for row in rows])
        source_cases = []
        for match in matches_for_row:
            label = f"{match.workbook} / {match.sheet} / row {match.excel_row}"
            if label not in source_cases:
                source_cases.append(label)
        reference_type = build_reference_type(matches_for_row, module)
        themes = {match.theme for match in matches_for_row}
        boundary_scopes = []
        for row in rows:
            for scope_name in boundary_scope_names(row, scope.name, scopes):
                if scope_name not in boundary_scopes:
                    boundary_scopes.append(scope_name)
        confirmation_reasons = build_confirmation_reasons(
            reference_type,
            boundary_scopes,
            themes,
            severity,
            occurrence,
            detection,
        )
        confirmation_status = build_confirmation_status(confirmation_reasons)
        rating_basis = build_rating_basis(
            themes,
            reference_type,
            severity,
            occurrence,
            detection,
        )
        reviewer_focus = build_reviewer_focus(reference_type, boundary_scopes, occurrence, detection)

        draft_rows.append(
            DraftRow(
                scope=scope.name,
                analysis_object=analysis_object,
                function=function,
                failure_mode=failure_mode,
                effect=effect,
                severity=severity,
                cause=cause,
                occurrence=occurrence,
                current_controls=current_controls,
                detection=detection,
                rpn=rpn,
                recommended_actions=recommended_actions,
                owner=owner,
                target_date=target_date,
                confirmation_status=confirmation_status,
                rating_basis=rating_basis,
                reference_type=reference_type,
                source_cases=source_cases,
                confirmation_reasons=confirmation_reasons,
                reviewer_focus=reviewer_focus,
                boundary_scopes=boundary_scopes,
                max_match_score=max(match.score for match in matches_for_row),
                max_scope_hits=max(scope_hit_count(row, scope.query_terms) for row in rows),
            )
        )

    draft_rows.sort(
        key=lambda item: (
            -(safe_int(item.rpn) or -1),
            -item.max_scope_hits,
            -item.max_match_score,
            item.analysis_object,
            item.failure_mode,
        )
    )
    return draft_rows


def format_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def safe_sheet_title(title: str, used_titles: set[str]) -> str:
    cleaned = re.sub(r"[\[\]\:*?/\\]", "_", title).strip() or "Sheet"
    cleaned = cleaned[:31]
    if cleaned not in used_titles:
        used_titles.add(cleaned)
        return cleaned

    index = 2
    while True:
        suffix = f"_{index}"
        candidate = f"{cleaned[: 31 - len(suffix)]}{suffix}"
        if candidate not in used_titles:
            used_titles.add(candidate)
            return candidate
        index += 1


def write_sheet_table(ws: Any, headers: list[str], rows: list[list[Any]], freeze: str = "A2") -> None:
    header_fill = PatternFill(fill_type="solid", fgColor="D9EAD3")
    header_font = Font(bold=True)
    wrap_alignment = Alignment(vertical="top", wrap_text=True)

    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = wrap_alignment

    for row in rows:
        ws.append(row)

    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = wrap_alignment

    if ws.max_row >= 1 and ws.max_column >= 1:
        ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = freeze

    for column_cells in ws.columns:
        letter = get_column_letter(column_cells[0].column)
        max_length = 0
        for cell in column_cells:
            text = "" if cell.value is None else str(cell.value)
            longest = max((len(line) for line in text.splitlines()), default=0)
            max_length = max(max_length, longest)
        ws.column_dimensions[letter].width = min(max(max_length + 2, 12), 48)


def render_excel_workbook(
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
    excel_path: Path,
) -> None:
    confirmation_queue = build_confirmation_queue(scope_rows)
    top_risks = build_top_risks(scope_rows)
    suggested_actions = build_suggested_actions(scope_rows)
    source_trace = build_source_trace(scope_rows)

    workbook = Workbook()
    used_titles: set[str] = set()

    overview = workbook.active
    overview.title = safe_sheet_title("概览", used_titles)
    overview["A1"] = "模块"
    overview["B1"] = module
    overview["A2"] = "FMEA 类型"
    overview["B2"] = fmea_type
    overview["A3"] = "Scope 数量"
    overview["B3"] = len(scopes)
    overview["A4"] = "草稿行数"
    overview["B4"] = sum(len(rows) for rows in scope_rows.values())
    overview["A5"] = "确认队列数"
    overview["B5"] = len(confirmation_queue)
    overview["A6"] = "输入摘要"
    overview["B6"] = input_text[:1000] + ("..." if len(input_text) > 1000 else "")
    for row in overview.iter_rows(min_row=1, max_row=6, min_col=1, max_col=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    overview.column_dimensions["A"].width = 16
    overview.column_dimensions["B"].width = 90

    scope_plan = workbook.create_sheet(safe_sheet_title("Scope规划", used_titles))
    write_sheet_table(
        scope_plan,
        ["Scope", "检索关键词", "来源", "命中数", "说明"],
        [
            [
                scope.name,
                " / ".join(scope.query_terms or scope.extracted_terms),
                "auto" if scope.auto_suggested else "manual",
                scope.hit_count,
                scope.reason,
            ]
            for scope in scopes
        ],
    )

    for index, scope in enumerate(scopes, start=1):
        ws = workbook.create_sheet(safe_sheet_title(f"{index:02d}-{scope.name}", used_titles))
        rows = scope_rows.get(scope.name, [])
        write_sheet_table(
            ws,
            [
                "Scope",
                "Analysis object",
                "Function or requirement",
                "Failure mode",
                "Failure effect",
                "S",
                "Cause or mechanism",
                "O",
                "Current controls",
                "D",
                "RPN",
                "Recommended actions",
                "Owner",
                "Target date",
                "Confirmation status",
                "Review comment",
                "Rating basis",
                "Reference type",
                "Source case",
            ],
            [
                [
                    row.scope,
                    row.analysis_object,
                    row.function,
                    row.failure_mode,
                    row.effect,
                    row.severity,
                    row.cause,
                    row.occurrence,
                    row.current_controls,
                    row.detection,
                    row.rpn,
                    row.recommended_actions,
                    row.owner,
                    row.target_date,
                    row.confirmation_status,
                    row.review_comment,
                    row.rating_basis,
                    row.reference_type,
                    "; ".join(row.source_cases),
                ]
                for row in rows
            ]
            or [
                [
                    scope.name,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "未召回到足够案例，建议补充输入或手工定义 scope。",
                    "",
                    "",
                    "needs expert confirmation",
                    "",
                    "需要补充输入后再判断",
                    "broader analogy",
                    "",
                ]
            ],
        )

    confirmation_ws = workbook.create_sheet(safe_sheet_title("确认队列", used_titles))
    write_sheet_table(
        confirmation_ws,
        ["Scope", "Row key", "Why confirmation is needed", "Suggested reviewer focus", "Review comment", "Reference type", "Source case"],
        [
            [
                item.scope,
                item.row_key,
                item.why_confirmation_is_needed,
                item.suggested_reviewer_focus,
                item.review_comment,
                item.reference_type,
                "; ".join(item.source_cases),
            ]
            for item in confirmation_queue
        ]
        or [["", "", "当前没有额外确认队列，仍建议在评审中校准 O/D。", "", "", "", ""]],
    )

    top_risk_ws = workbook.create_sheet(safe_sheet_title("Top风险", used_titles))
    write_sheet_table(
        top_risk_ws,
        ["Scope", "Row key", "Failure mode", "Current RPN", "Why it matters", "First action candidate", "Reference type"],
        [
            [
                item["scope"],
                item["row_key"],
                item["failure_mode"],
                item["current_rpn"],
                item["why_it_matters"],
                item["first_action_candidate"],
                item["reference_type"],
            ]
            for item in top_risks
        ],
    )

    action_ws = workbook.create_sheet(safe_sheet_title("建议动作", used_titles))
    write_sheet_table(
        action_ws,
        [
            "Scope",
            "Row key",
            "Current RPN",
            "Recommended action",
            "Owner",
            "Target date",
            "Confirmation status",
            "Review comment",
            "Reference type",
            "Source case",
        ],
        [
            [
                item["scope"],
                item["row_key"],
                item["current_rpn"],
                item["recommended_action"],
                item["owner"],
                item["target_date"],
                item["confirmation_status"],
                item["review_comment"],
                item["reference_type"],
                item["source_case"],
            ]
            for item in suggested_actions
        ],
    )

    trace_ws = workbook.create_sheet(safe_sheet_title("来源追踪", used_titles))
    write_sheet_table(
        trace_ws,
        ["Scope", "Row key", "Reference type", "Source case"],
        [
            [
                item["scope"],
                item["row_key"],
                item["reference_type"],
                "; ".join(item["source_cases"]),
            ]
            for item in source_trace
        ],
    )

    excel_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(excel_path)


def render_markdown(
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
) -> str:
    confirmation_queue = build_confirmation_queue(scope_rows)
    top_risks = build_top_risks(scope_rows)
    suggested_actions = build_suggested_actions(scope_rows)
    source_trace = build_source_trace(scope_rows)
    lines = [
        f"# {module or '未命名模块'} 首版 {fmea_type} 草稿",
        "",
        "- 生成方式: `draft_fmea_from_cases.py`",
        f"- 模块: `{module}`" if module else "- 模块: 未指定",
        f"- FMEA 类型: `{fmea_type}`",
        f"- 输入长度: `{len(input_text)}` 字符",
        "",
        "## 输入摘要",
        "",
        "> " + format_md_cell(input_text[:400] + ("..." if len(input_text) > 400 else "")),
        "",
        "## Scope 规划",
        "",
        "| Scope | 检索关键词 | 来源 | 命中数 | 说明 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for scope in scopes:
        terms = scope.query_terms or scope.extracted_terms
        source = "auto" if scope.auto_suggested else "manual"
        lines.append(
            f"| {format_md_cell(scope.name)} | {format_md_cell(' / '.join(terms))} | {source} | {scope.hit_count} | {format_md_cell(scope.reason)} |"
        )

    for scope in scopes:
        rows = scope_rows.get(scope.name, [])
        lines.extend(
            [
                "",
                f"## {scope.name}",
                "",
                "| Scope | Analysis object | Function or requirement | Failure mode | Failure effect | S | Cause or mechanism | O | Current controls | D | RPN | Recommended actions | Confirmation status | Review comment | Rating basis | Reference type | Source case |",
                "| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        if not rows:
            lines.append("|  |  |  |  |  |  |  |  |  |  |  | 未召回到足够案例，建议补充输入或手工定义 scope。 | needs expert confirmation |  | 需要补充输入后再判断 | broader analogy |  |")
            continue
        for row in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        format_md_cell(row.scope),
                        format_md_cell(row.analysis_object),
                        format_md_cell(row.function),
                        format_md_cell(row.failure_mode),
                        format_md_cell(row.effect),
                        format_md_cell(row.severity),
                        format_md_cell(row.cause),
                        format_md_cell(row.occurrence),
                        format_md_cell(row.current_controls),
                        format_md_cell(row.detection),
                        format_md_cell(row.rpn),
                        format_md_cell(row.recommended_actions),
                        format_md_cell(row.confirmation_status),
                        format_md_cell(row.review_comment),
                        format_md_cell(row.rating_basis),
                        format_md_cell(row.reference_type),
                        format_md_cell("; ".join(row.source_cases)),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Top Risks",
            "",
            "| Scope | Row key | Failure mode | Current RPN | Why it matters | First action candidate | Reference type |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for item in top_risks:
        lines.append(
            f"| {format_md_cell(item['scope'])} | {format_md_cell(item['row_key'])} | {format_md_cell(item['failure_mode'])} | {format_md_cell(item['current_rpn'])} | {format_md_cell(item['why_it_matters'])} | {format_md_cell(item['first_action_candidate'])} | {format_md_cell(item['reference_type'])} |"
        )

    lines.extend(
        [
            "",
            "## Rows Needing Confirmation",
            "",
            "| Scope | Row key | Why confirmation is needed | Suggested reviewer focus | Review comment | Reference type | Source case |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not confirmation_queue:
        lines.append("|  |  | 当前没有额外确认队列，仍建议在评审中校准 O/D。 |  |  |  |  |")
    else:
        for item in confirmation_queue[:12]:
            lines.append(
                f"| {format_md_cell(item.scope)} | {format_md_cell(item.row_key)} | {format_md_cell(item.why_confirmation_is_needed)} | {format_md_cell(item.suggested_reviewer_focus)} | {format_md_cell(item.review_comment)} | {format_md_cell(item.reference_type)} | {format_md_cell('; '.join(item.source_cases))} |"
            )

    lines.extend(
        [
            "",
            "## Suggested Actions",
            "",
            "| Scope | Row key | Current RPN | Recommended action | Owner | Target date | Confirmation status | Review comment | Reference type | Source case |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in suggested_actions[:12]:
        lines.append(
            f"| {format_md_cell(item['scope'])} | {format_md_cell(item['row_key'])} | {format_md_cell(item['current_rpn'])} | {format_md_cell(item['recommended_action'])} | {format_md_cell(item['owner'])} | {format_md_cell(item['target_date'])} | {format_md_cell(item['confirmation_status'])} | {format_md_cell(item['review_comment'])} | {format_md_cell(item['reference_type'])} | {format_md_cell(item['source_case'])} |"
        )

    lines.extend(
        [
            "",
            "## Source Trace",
            "",
            "| Scope | Row key | Reference type | Source case |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in source_trace:
        lines.append(
            f"| {format_md_cell(item['scope'])} | {format_md_cell(item['row_key'])} | {format_md_cell(item['reference_type'])} | {format_md_cell('; '.join(item['source_cases']))} |"
        )

    return "\n".join(lines) + "\n"


def build_json_payload(
    module: str,
    fmea_type: str,
    input_text: str,
    scopes: list[ScopeDefinition],
    scope_rows: dict[str, list[DraftRow]],
) -> dict[str, Any]:
    confirmation_queue = build_confirmation_queue(scope_rows)
    top_risks = build_top_risks(scope_rows)
    suggested_actions = build_suggested_actions(scope_rows)
    source_trace = build_source_trace(scope_rows)
    return {
        "module": module,
        "fmea_type": fmea_type,
        "input_text": input_text,
        "scopes": [asdict(scope) for scope in scopes],
        "rows": [asdict(row) for rows in scope_rows.values() for row in rows],
        "confirmation_queue": [asdict(item) for item in confirmation_queue],
        "top_risks": top_risks,
        "suggested_actions": suggested_actions,
        "source_trace": source_trace,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft a first FMEA table from natural-language input and historical cases.")
    parser.add_argument("--module", required=True, help="Module name or analysis object.")
    parser.add_argument("--fmea-type", default="DFMEA", help="FMEA type, default is DFMEA.")
    parser.add_argument("--input-file", help="Path to a UTF-8 text file containing the natural-language input.")
    parser.add_argument("--input-text", help="Natural-language input text.")
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Optional scope definition in the form 'Scope Name::keyword1 keyword2'. Repeatable.",
    )
    parser.add_argument("--top-k", type=int, default=12, help="Number of source matches to keep per scope.")
    parser.add_argument("--excel-out", help="Optional path to save the generated Excel workbook.")
    parser.add_argument("--markdown-out", help="Optional path to save the generated Markdown draft.")
    parser.add_argument("--json-out", help="Optional path to save the generated JSON draft.")
    args = parser.parse_args()

    input_text = load_input_text(args)
    extracted_terms = extract_query_terms(input_text, args.module)

    scopes = [parse_scope(raw_scope) for raw_scope in args.scope]
    if not scopes:
        scopes = suggest_scopes(args.module, input_text, extracted_terms)
        if not scopes:
            scopes = [
                ScopeDefinition(
                    name=f"{args.module}整体范围",
                    query_terms=extracted_terms[:12],
                    extracted_terms=extracted_terms,
                    auto_suggested=True,
                    hit_count=0,
                    reason="fallback: no strong scope profile matched",
                )
            ]
    else:
        for scope in scopes:
            scope.extracted_terms = [term for term in extracted_terms if term in scope.query_terms or term in input_text]

    scope_rows: dict[str, list[DraftRow]] = {}
    for scope in scopes:
        query = " ".join(scope.query_terms or scope.extracted_terms)
        matches = collect_matches(query, args.module)
        matches = [match for match in matches if match.theme in ALLOWED_THEMES][: args.top_k]
        scope_rows[scope.name] = aggregate_rows(scope, scopes, matches, args.module)

    markdown = render_markdown(args.module, args.fmea_type, input_text, scopes, scope_rows)
    payload = build_json_payload(args.module, args.fmea_type, input_text, scopes, scope_rows)

    if args.excel_out:
        excel_path = Path(args.excel_out)
        render_excel_workbook(args.module, args.fmea_type, input_text, scopes, scope_rows, excel_path)

    if args.markdown_out:
        markdown_path = Path(args.markdown_out)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
