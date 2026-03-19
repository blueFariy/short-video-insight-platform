"""
Prompt Template Management Service
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger


class PromptTemplate:
    """Prompt template"""

    def __init__(self, id: str, name: str, description: str, template: str, category: str = "general"):
        self.id = id
        self.name = name
        self.description = description
        self.template = template
        self.category = category


class PromptTemplateService:
    """Prompt template management service"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {
            "golden_hook": PromptTemplate(
                id="golden_hook",
                name="黄金3秒开场",
                description="提取视频开场的黄金3秒文案",
                category="hook",
                template="""你是一位短视频营销专家。你的任务是从视频脚本中提取"黄金3秒"开场文案。

请分析视频的开场部分，提取：
1. 开头3秒的核心吸引力文案
2. 开场白的特点（提问/悬念/痛点/反常识等）
3. 为什么这个开场能抓住观众注意力

请用JSON格式返回：
{
    "hook_text": "提取的黄金3秒文案",
    "hook_type": "开场类型（提问/悬念/痛点/反常识/情绪共鸣/其他）",
    "analysis": "为什么有效",
    "suggestions": "优化建议"
}"""
            ),
            "script_structure": PromptTemplate(
                id="script_structure",
                name="脚本结构分析",
                description="分析视频脚本的内容结构和节奏",
                category="structure",
                template="""你是一位内容结构分析师。你的任务是分析短视频的脚本结构。

请分析视频脚本的结构：
1. 开场（黄金3秒）
2. 铺垫/痛点陈述
3. 核心内容/解决方案
4. 情感高潮
5. 结尾/行动号召

请用JSON格式返回：
{
    "segments": [
        {"time": "时间段", "type": "类型", "content": "内容概述"}
    ],
    "structure_score": "结构评分 0-100",
    "strengths": ["优势1", "优势2"],
    "improvements": ["改进建议1", "改进建议2"]
}"""
            ),
            "sentiment_analysis": PromptTemplate(
                id="sentiment_analysis",
                name="评论区情感分析",
                description="分析评论区用户评论的情感倾向",
                category="sentiment",
                template="""你是一位情感分析专家。你的任务是分析短视频评论区用户评论的情感倾向。

请分析以下评论的情感：
1. 统计正面、中性、负面评论数量
2. 提取用户最关注的点
3. 分析评论中的情绪关键词

请用JSON格式返回：
{
    "total_comments": 总评论数,
    "positive_count": 正面评论数,
    "neutral_count": 中性评论数,
    "negative_count": 负面评论数,
    "sentiment_ratio": {"positive": 0.x, "neutral": 0.x, "negative": 0.x},
    "top_positive_keywords": ["关键词1"],
    "top_negative_keywords": ["关键词1"],
    "user_insights": "用户洞察总结"
}"""
            ),
            "comprehensive": PromptTemplate(
                id="comprehensive",
                name="综合爆款分析",
                description="生成完整的爆款分析报告",
                category="analysis",
                template="""你是一位短视频爆款分析师。你的任务是全面分析短视频的爆款潜力。

请从以下维度分析：
1. 黄金3秒开场
2. 内容价值
3. 情感触发
4. 行动号召
5. 整体结构

请用JSON格式返回：
{
    "overall_score": 总分0-100,
    "dimensions": {
        "hook_score": 开场评分0-100,
        "value_score": 价值评分0-100,
        "emotion_score": 情感评分0-100,
        "cta_score": 行动号召评分0-100,
        "structure_score": 结构评分0-100
    },
    "highlights": ["亮点1", "亮点2"],
    "improvements": ["改进点1", "改进点2"],
    "summary": "总结"
}"""
            ),
            "content_enhancement": PromptTemplate(
                id="content_enhancement",
                name="内容优化建议",
                description="提供内容优化建议",
                category="optimization",
                template="""你是一位内容优化专家。请分析以下视频内容，并提供优化建议。

分析维度：
1. 标题吸引力
2. 开头吸引力
3. 内容价值
4. 情感共鸣
5. 结尾行动号召

请用JSON格式返回：
{
    "current_strengths": ["当前亮点1", "当前亮点2"],
    "improvements": [
        {"area": "优化区域", "current": "现状", "suggestion": "建议", "priority": "高/中/低"}
    ],
    "actionable_tips": ["可执行的优化技巧1", "可执行的优化技巧2"]
}"""
            ),
            "trend_prediction": PromptTemplate(
                id="trend_prediction",
                name="趋势预测",
                description="预测内容趋势和受众兴趣",
                category="prediction",
                template="""你是一位内容趋势分析师。请基于以下信息预测内容趋势。

请分析：
1. 目标受众的兴趣点
2. 可能的热门话题
3. 内容趋势预测

请用JSON格式返回：
{
    "target_audience": "目标受众描述",
    "interest_points": ["兴趣点1", "兴趣点2"],
    "trend_predictions": ["预测1", "预测2"],
    "opportunities": ["机会点1", "机会点2"]
}"""
            )
        }

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """List all templates, optionally filtered by category"""
        if category:
            return [t for t in self.templates.values() if t.category == category]
        return list(self.templates.values())

    def create_template(
        self,
        id: str,
        name: str,
        description: str,
        template: str,
        category: str = "general"
    ) -> PromptTemplate:
        """Create a new template"""
        new_template = PromptTemplate(id, name, description, template, category)
        self.templates[id] = new_template
        return new_template

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """Update an existing template"""
        existing = self.templates.get(template_id)
        if not existing:
            return None

        if name:
            existing.name = name
        if description:
            existing.description = description
        if template:
            existing.template = template
        if category:
            existing.category = category

        return existing

    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False


prompt_template_service = PromptTemplateService()
