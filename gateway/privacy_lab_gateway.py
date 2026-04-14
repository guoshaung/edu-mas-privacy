from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/privacy", tags=["privacy-lab"])
compat_router = APIRouter(tags=["privacy-lab-compat"])


class PrivacyAttackDemoRequest(BaseModel):
    attack_name: str = Field(..., min_length=1)
    raw_prompt: str = Field(..., min_length=1)
    student_name: str = "张三"
    student_id: str = "20260001"
    raw_profile: dict[str, Any] = Field(default_factory=dict)


class LogEntry(BaseModel):
    step: str
    status: str
    detail: str


class CompareItem(BaseModel):
    field: str
    before: str
    after: str
    protection: str


class PrivacyAttackDemoResponse(BaseModel):
    attack_name: str
    blocked: bool
    risk_score_before: float
    risk_score_after: float
    attacker_view_before: str
    attacker_view_after: str
    compare_panel: List[CompareItem]
    abac_timeline: List[LogEntry]
    user_notice: str


ROLE_LEVELS = {
    "student_basic": 1,
    "student_verified": 2,
    "teacher_basic": 3,
    "teacher_curator": 4,
    "system_agent": 5,
    "system_high_trust_agent": 6,
}


RESOURCE_POLICY = {
    "student_raw_profile": {
        "classification": "P3",
        "required_role": "system_high_trust_agent",
        "allowed_phase": {"Diagnosis"},
        "fallback": "summary_only",
    },
    "psychology_raw_answers": {
        "classification": "P3",
        "required_role": "system_high_trust_agent",
        "allowed_phase": {"Diagnosis"},
        "fallback": "masked",
    },
    "teacher_bank_fulltext": {
        "classification": "C3",
        "required_role": "teacher_curator",
        "allowed_phase": {"Mining"},
        "fallback": "substitute_generation",
    },
    "teacher_bank_summary": {
        "classification": "C2",
        "required_role": "teacher_basic",
        "allowed_phase": {"Mining", "Tutoring"},
        "fallback": "summary_only",
    },
}


def _default_profile(request: PrivacyAttackDemoRequest) -> dict[str, Any]:
    return {
        "student_name": request.student_name,
        "student_id": request.student_id,
        "gender": "男",
        "class_name": "高一(2)班",
        "personality": "INTJ",
        "stress_level": "Medium",
        "knowledge_graph_level": "中等",
        "weakness_tags": ["dimension_mismatch", "calculation_carelessness"],
        "counseling_flag": "none",
        "resource_access_group": "math_a",
    }


def _response(
    attack_name: str,
    risk_before: float,
    risk_after: float,
    before_view: str,
    after_view: str,
    compare_panel: List[CompareItem],
    timeline: List[LogEntry],
    notice: str,
    blocked: bool = True,
) -> PrivacyAttackDemoResponse:
    return PrivacyAttackDemoResponse(
        attack_name=attack_name,
        blocked=blocked,
        risk_score_before=risk_before,
        risk_score_after=risk_after,
        attacker_view_before=before_view,
        attacker_view_after=after_view,
        compare_panel=compare_panel,
        abac_timeline=timeline,
        user_notice=notice,
    )


def _prompt_injection_response(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    raw_profile = request.raw_profile or _default_profile(request)
    compare_panel = [
        CompareItem(field="姓名", before=str(raw_profile.get("student_name", request.student_name)), after="匿名学生-A01", protection="身份匿名化处理"),
        CompareItem(field="学号", before=str(raw_profile.get("student_id", request.student_id)), after="已隐藏", protection="直接标识符屏蔽"),
        CompareItem(field="心理压力", before=str(raw_profile.get("stress_level", "Medium")), after="区间化风险: 中等", protection="敏感属性模糊化"),
        CompareItem(field="薄弱标签", before=", ".join(raw_profile.get("weakness_tags", ["dimension_mismatch"])), after="仅保留学习相关薄弱项", protection="最小必要数据流转"),
    ]
    timeline = [
        LogEntry(step="攻击请求进入隐私网关", status="received", detail="系统检测到提示注入式请求，准备进入联合鉴权。"),
        LogEntry(step="提示注入模式识别", status="flagged", detail="发现越权关键词，例如“忽略规则”“返回原始画像”“暴露身份”。"),
        LogEntry(step="ABAC 联合判定", status="blocked", detail="当前请求无权访问原始身份字段，仅允许读取脱敏后的最小必要特征。"),
        LogEntry(step="语义重构与脱敏保护", status="applied", detail="直接标识被替换，心理与个体属性被区间化和模糊化处理。"),
        LogEntry(step="云端智能体可见内容", status="safe", detail="云端仅接收到匿名后的学习相关特征，无法还原真实学生身份。"),
    ]
    return _response(
        attack_name="prompt_injection",
        risk_before=0.86,
        risk_after=0.24,
        before_view="攻击者试图让系统忽略安全规则，并返回学生原始画像、学号和心理标签。",
        after_view="系统仅返回匿名学生编号、脱敏后的学习偏好和区间化风险等级，无法定位到真实学生。",
        compare_panel=compare_panel,
        timeline=timeline,
        notice="你的姓名、学号和敏感心理标签没有被直接暴露。当前展示的是经过隐私网关保护后的安全结果。",
    )


def _identity_recovery_response(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    raw_profile = request.raw_profile or _default_profile(request)
    compare_panel = [
        CompareItem(field="姓名 + 班级", before=f"{raw_profile.get('student_name')} / {raw_profile.get('class_name')}", after="匿名学生-A01 / 年级级别", protection="去标识化与班级泛化"),
        CompareItem(field="身份指纹", before=f"{raw_profile.get('gender')} + {raw_profile.get('personality')}", after="仅保留学习风格标签", protection="高识别属性折叠"),
        CompareItem(field="画像关联键", before=str(raw_profile.get("student_id")), after="一次性会话别名", protection="会话级伪名替代"),
        CompareItem(field="知识图谱等级", before=str(raw_profile.get("knowledge_graph_level", "中等")), after="能力区间: 进阶中", protection="能力等级区间化"),
    ]
    timeline = [
        LogEntry(step="身份恢复请求进入网关", status="received", detail="检测到攻击者试图通过多字段拼接恢复真实身份。"),
        LogEntry(step="准标识符组合分析", status="flagged", detail="系统识别出姓名、班级、性别和人格标签可构成高识别组合。"),
        LogEntry(step="重识别风险计算", status="blocked", detail="重识别风险超过阈值，仅允许输出匿名别名和区间信息。"),
        LogEntry(step="伪名映射生效", status="applied", detail="将真实身份映射为短时会话别名，阻断跨会话追踪。"),
        LogEntry(step="结果降级返回", status="safe", detail="仅返回去标识后的画像摘要，身份恢复链路被切断。"),
    ]
    return _response(
        attack_name="identity_recovery",
        risk_before=0.82,
        risk_after=0.22,
        before_view="攻击者试图联合姓名、班级、性格和能力标签恢复学生真实身份。",
        after_view="系统仅返回匿名别名、区间化能力等级和泛化后的班级信息，无法锁定个人。",
        compare_panel=compare_panel,
        timeline=timeline,
        notice="系统会把可能形成身份指纹的字段组合拆开并泛化，因此即使攻击者拿到部分标签，也难以恢复到具体学生。",
    )


def _attribute_inference_response(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    raw_profile = request.raw_profile or _default_profile(request)
    compare_panel = [
        CompareItem(field="心理压力", before=str(raw_profile.get("stress_level", "Medium")), after="学习节奏建议: 中等", protection="敏感属性转任务属性"),
        CompareItem(field="咨询标记", before=str(raw_profile.get("counseling_flag", "none")), after="未开放", protection="敏感字段不可推断"),
        CompareItem(field="薄弱标签", before=", ".join(raw_profile.get("weakness_tags", [])), after="仅保留当前主题弱项", protection="按阶段裁剪"),
        CompareItem(field="人格标签", before=str(raw_profile.get("personality", "INTJ")), after="学习风格: 可视化偏好", protection="高敏属性抽象化"),
    ]
    timeline = [
        LogEntry(step="属性推断请求进入网关", status="received", detail="检测到攻击者试图从学习行为反推出心理与个体属性。"),
        LogEntry(step="属性敏感度识别", status="flagged", detail="心理状态、咨询标记和人格标签被识别为高敏感字段。"),
        LogEntry(step="任务相关性筛选", status="applied", detail="系统仅保留当前辅导任务必需的低敏学习特征。"),
        LogEntry(step="推断链条切断", status="blocked", detail="会导致敏感属性反推出的组合字段被降维和抽象。"),
        LogEntry(step="安全结果下发", status="safe", detail="云端只能看到教学相关的抽象标签，无法反推出原始隐私属性。"),
    ]
    return _response(
        attack_name="attribute_inference",
        risk_before=0.78,
        risk_after=0.26,
        before_view="攻击者试图根据学习行为、薄弱点和表达方式推断学生的心理压力与咨询状态。",
        after_view="系统仅保留任务相关的学习节奏建议和主题弱项，切断了对高敏属性的反推路径。",
        compare_panel=compare_panel,
        timeline=timeline,
        notice="即使系统需要利用学习特征进行教学，也会把高敏感个人属性转换成抽象任务属性，避免被反向推断。",
    )


def _membership_inference_response(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    raw_profile = request.raw_profile or _default_profile(request)
    compare_panel = [
        CompareItem(field="资源访问组", before=str(raw_profile.get("resource_access_group", "math_a")), after="课程级访问组", protection="群组标签泛化"),
        CompareItem(field="参与状态", before="在某高敏样本集合内", after="仅显示已授权课程成员", protection="成员集合模糊化"),
        CompareItem(field="历史频率", before="高频参与", after="常规学习活跃度", protection="统计摘要替代"),
        CompareItem(field="会话标签", before=str(raw_profile.get("student_id")), after="短期匿名会话", protection="成员证明去绑定"),
    ]
    timeline = [
        LogEntry(step="成员推断请求进入网关", status="received", detail="攻击者尝试判断学生是否属于某个高敏学习/心理样本集合。"),
        LogEntry(step="集合成员性检测", status="flagged", detail="系统识别到该请求试图利用响应差异判断成员身份。"),
        LogEntry(step="分布平滑处理", status="applied", detail="对结果做群组级平滑与一致化，避免成员与非成员响应差异过大。"),
        LogEntry(step="集合标签泛化", status="blocked", detail="高敏集合被映射为课程级或主题级群组，拒绝返回真实成员关系。"),
        LogEntry(step="风险审计记录", status="safe", detail="仅返回授权范围内的粗粒度参与信息，并记录本次探测行为。"),
    ]
    return _response(
        attack_name="membership_inference",
        risk_before=0.74,
        risk_after=0.21,
        before_view="攻击者试图判断该学生是否属于某个特定高敏群体或重点观察样本集合。",
        after_view="系统只暴露课程级群组信息和统一化响应，无法据此确认学生是否属于高敏集合。",
        compare_panel=compare_panel,
        timeline=timeline,
        notice="系统会削弱成员与非成员之间的响应差异，因此外部无法通过多次探测确定你是否属于某个敏感集合。",
    )


def _linkage_attack_response(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    raw_profile = request.raw_profile or _default_profile(request)
    compare_panel = [
        CompareItem(field="跨页标识", before=str(raw_profile.get("student_id")), after="页面独立匿名标识", protection="多页面去关联化"),
        CompareItem(field="行为轨迹", before="诊断→规划→辅导→检验 全链路", after="仅阶段级摘要", protection="时间链路裁剪"),
        CompareItem(field="题库访问记录", before="可与教师题库记录联结", after="仅主题级命中信息", protection="跨域联结阻断"),
        CompareItem(field="画像标签", before=f"{raw_profile.get('personality')} / {raw_profile.get('class_name')}", after="抽象学习画像", protection="高关联标签抽象化"),
    ]
    timeline = [
        LogEntry(step="链接重识别请求进入网关", status="received", detail="攻击者试图联合多个页面、多个阶段和外部日志进行记录对齐。"),
        LogEntry(step="跨域联结分析", status="flagged", detail="系统发现当前请求涉及学生端、教师题库端和会话日志的多源拼接。"),
        LogEntry(step="会话隔离与别名轮换", status="applied", detail="不同页面和阶段使用不同匿名标识，阻断记录对齐。"),
        LogEntry(step="链路摘要化返回", status="blocked", detail="全链路行为被降级为阶段级摘要，避免形成可链接轨迹。"),
        LogEntry(step="安全视图生成", status="safe", detail="返回的仅是单阶段、单任务的抽象信息，无法跨域重识别。"),
    ]
    return _response(
        attack_name="linkage_attack",
        risk_before=0.80,
        risk_after=0.23,
        before_view="攻击者试图把学生端页面记录、教师题库访问记录和多阶段日志拼接，重建完整身份轨迹。",
        after_view="系统对不同页面、不同阶段采用独立匿名标识，并仅返回阶段级摘要，无法完成跨域链接。",
        compare_panel=compare_panel,
        timeline=timeline,
        notice="系统会切断跨页面、跨阶段、跨域的稳定关联键，所以即使攻击者掌握多份日志，也难以把它们重新拼成你的完整轨迹。",
    )


def _privilege_escalation_response() -> PrivacyAttackDemoResponse:
    subject_role = "student_basic"
    target_resource = "teacher_bank_fulltext"
    current_phase = "Tutoring"
    policy = RESOURCE_POLICY[target_resource]
    required_role = policy["required_role"]
    fallback = policy["fallback"]

    compare_panel = [
        CompareItem(field="请求主体", before=subject_role, after=required_role, protection="角色等级匹配校验"),
        CompareItem(field="目标资源", before=target_resource, after=policy["classification"], protection="资源敏感度分级"),
        CompareItem(field="允许阶段", before=current_phase, after=", ".join(sorted(policy["allowed_phase"])), protection="阶段约束控制"),
        CompareItem(field="系统返回", before="教师题库原题全文 + 讲义原文", after="知识点摘要 + 替代练习题", protection="越权后降级为安全替代内容"),
    ]
    timeline = [
        LogEntry(step="越权请求进入治理层", status="received", detail="学生端尝试绕过正常流程，直接请求 AG4 返回教师题库全文。"),
        LogEntry(step="主体角色识别", status="flagged", detail=f"当前主体角色为 {subject_role}，低于访问 {target_resource} 所需角色 {required_role}。"),
        LogEntry(step="阶段约束检查", status="blocked", detail=f"当前阶段为 {current_phase}，而该资源仅允许在 {', '.join(sorted(policy['allowed_phase']))} 阶段访问。"),
        LogEntry(step="版权合规联合判定", status="applied", detail="目标资源属于高敏版权内容 C3，禁止向学生侧直接返回原文。"),
        LogEntry(step="安全替代输出", status="safe", detail=f"系统执行 {fallback} 策略，不返回原始资源，只返回摘要与替代性生成内容。"),
    ]
    return _response(
        attack_name="privilege_escalation",
        risk_before=0.88,
        risk_after=0.18,
        before_view="攻击者希望以学生身份直接读取教师题库中的原题全文、讲义原文和高权限内部资源。",
        after_view="系统拒绝原文访问，只返回面向当前学习任务的知识点摘要和替代练习内容。",
        compare_panel=compare_panel,
        timeline=timeline,
        notice="即使攻击者试图越权索取高权限资源，系统也会同时检查角色等级、资源敏感度、当前阶段和版权风险，最终只返回安全降级后的内容。",
    )


def _build_attack_response(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    attack_name = request.attack_name.strip().lower()
    if attack_name == "prompt_injection":
        return _prompt_injection_response(request)
    if attack_name == "identity_recovery":
        return _identity_recovery_response(request)
    if attack_name == "attribute_inference":
        return _attribute_inference_response(request)
    if attack_name == "membership_inference":
        return _membership_inference_response(request)
    if attack_name == "linkage_attack":
        return _linkage_attack_response(request)
    if attack_name == "privilege_escalation":
        return _privilege_escalation_response()

    return _response(
        attack_name=attack_name,
        risk_before=0.50,
        risk_after=0.50,
        before_view="当前攻击类型暂未接入演示接口。",
        after_view="请先选择已接入的隐私攻击类型进行演示。",
        compare_panel=[],
        timeline=[],
        notice="该攻击方式暂未在云端网关中实现。",
        blocked=False,
    )


@router.post("/attack-demo", response_model=PrivacyAttackDemoResponse)
@compat_router.post("/api/privacy/attack-demo", response_model=PrivacyAttackDemoResponse, include_in_schema=False)
async def privacy_attack_demo(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    return _build_attack_response(request)


@router.post("/prompt-injection-demo", response_model=PrivacyAttackDemoResponse)
@compat_router.post("/api/privacy/prompt-injection-demo", response_model=PrivacyAttackDemoResponse, include_in_schema=False)
async def prompt_injection_demo(request: PrivacyAttackDemoRequest) -> PrivacyAttackDemoResponse:
    return _prompt_injection_response(request)
