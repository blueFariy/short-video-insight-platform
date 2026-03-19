"""
Insight Analysis Service
"""
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

from app.services.ai_service import ai_service
from app.core.config import settings


class InsightService:
    """Insight analysis service"""

    def __init__(self):
        self.temp_dir = Path(settings.ANALYSIS_TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_golden_hook(
        self,
        video_title: str,
        video_script: str,
        keyframes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze golden 3-second hook

        Args:
            video_title: Video title
            video_script: Video script (ASR text)
            keyframes: Optional keyframe paths

        Returns:
            Analysis result
        """
        logger.info(f"Analyzing golden hook for: {video_title}")

        result = await ai_service.analyze_video(
            video_title=video_title,
            video_script=video_script,
            keyframes=keyframes or [],
            analysis_type="golden_3_seconds"
        )

        return {
            "type": "golden_hook",
            "data": result
        }

    async def analyze_script_structure(
        self,
        video_title: str,
        video_script: str,
        duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze script structure

        Args:
            video_title: Video title
            video_script: Video script
            duration: Video duration in seconds

        Returns:
            Analysis result
        """
        logger.info(f"Analyzing script structure for: {video_title}")

        result = await ai_service.analyze_video(
            video_title=video_title,
            video_script=video_script,
            keyframes=[],
            analysis_type="script_structure"
        )

        return {
            "type": "script_structure",
            "data": result
        }

    async def analyze_sentiment(
        self,
        comments: List[str],
        video_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze comment sentiment

        Args:
            comments: List of comments
            video_title: Optional video title

        Returns:
            Analysis result
        """
        logger.info(f"Analyzing sentiment for {len(comments)} comments")

        # Format comments for AI
        comments_text = "\n".join([f"- {c}" for c in comments[:100]])  # Limit to 100

        messages = [
            {"role": "user", "content": f"视频标题: {video_title or 'N/A'}\n\n评论内容:\n{comments_text}"}
        ]

        system_prompt = """你是一位情感分析专家。你的任务是分析短视频评论区用户评论的情感倾向。

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
    "top_positive_keywords": ["关键词1", "关键词2"],
    "top_negative_keywords": ["关键词1", "关键词2"],
    "user_insights": "用户洞察总结（50字以内）"
}"""

        response = await ai_service.chat(messages, system_prompt=system_prompt)

        # Parse response
        import re
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"raw_response": response}
        except Exception as e:
            logger.warning(f"Failed to parse sentiment response: {e}")
            result = {"raw_response": response}

        return {
            "type": "sentiment",
            "data": result
        }

    async def generate_comprehensive_report(
        self,
        video_title: str,
        video_script: str,
        comments: Optional[List[str]] = None,
        keyframes: Optional[List[str]] = None,
        duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report

        Args:
            video_title: Video title
            video_script: Video script
            comments: Optional comments
            keyframes: Optional keyframe paths
            duration: Video duration

        Returns:
            Comprehensive analysis report
        """
        logger.info(f"Generating comprehensive report for: {video_title}")

        # Run all analyses
        hook_result = await self.analyze_golden_hook(video_title, video_script, keyframes)
        structure_result = await self.analyze_script_structure(video_title, video_script, duration)

        sentiment_result = None
        if comments and len(comments) > 0:
            sentiment_result = await self.analyze_sentiment(comments, video_title)

        # Generate overall insights using AI
        messages = [
            {"role": "user", "content": f"""视频标题: {video_title}

视频脚本:
{video_script}

开场分析: {json.dumps(hook_result['data'], ensure_ascii=False)}
结构分析: {json.dumps(structure_result['data'], ensure_ascii=False)}
{f"情感分析: {json.dumps(sentiment_result['data'], ensure_ascii=False)}" if sentiment_result else ""}

请基于以上分析，生成一个综合的爆款分析报告。"""}
        ]

        system_prompt = """你是一位短视频爆款分析师。请基于各项分析结果，生成一份综合的爆款分析报告。

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
    "highlights": ["亮点1", "亮点2", "亮点3"],
    "improvements": ["改进点1", "改进点2", "改进点3"],
    "summary": "整体总结（100字以内）",
    "recommendations": ["建议1", "建议2"]
}"""

        response = await ai_service.chat(messages, system_prompt=system_prompt)

        # Parse response
        import re
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                overall = json.loads(json_match.group())
            else:
                overall = {"raw_response": response}
        except Exception as e:
            logger.warning(f"Failed to parse comprehensive response: {e}")
            overall = {"raw_response": response}

        return {
            "type": "comprehensive",
            "video_title": video_title,
            "duration": duration,
            "analysis": {
                "hook": hook_result["data"],
                "structure": structure_result["data"],
                "sentiment": sentiment_result["data"] if sentiment_result else None
            },
            "overall": overall
        }

    async def extract_script_segments(
        self,
        video_script: str,
        duration: int
    ) -> List[Dict[str, Any]]:
        """
        Extract script segments with timestamps

        Args:
            video_script: Full script
            duration: Video duration

        Returns:
            List of segments
        """
        messages = [
            {"role": "user", "content": f"""视频时长: {duration}秒

视频脚本:
{video_script}

请将视频脚本按照内容分段，并估计每个段落的时间范围。"""}
        ]

        system_prompt = """你是一位视频脚本分析师。请将视频脚本分割成多个有意义的段落。

请用JSON格式返回：
{
    "segments": [
        {"start_time": 0, "end_time": 5, "type": "开场", "content": "内容描述"},
        {"start_time": 5, "end_time": 15, "type": "铺垫", "内容描述"},
        ...
    ]
}

时间单位为秒。"""

        response = await ai_service.chat(messages, system_prompt=system_prompt)

        # Parse response
        import re
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("segments", [])
        except Exception as e:
            logger.warning(f"Failed to parse segments: {e}")

        return []


insight_service = InsightService()
