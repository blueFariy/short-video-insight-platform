"""
AI Service - Supports Zhipu GLM-4 and OpenAI GPT-4
"""
import json
import asyncio
from typing import Optional, Dict, Any, List
from loguru import logger

from app.core.config import settings
from app.core.exceptions import AIException


class AIService:
    """AI Service for video analysis"""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_model = settings.OPENAI_MODEL
        self.openai_base_url = settings.OPENAI_BASE_URL
        self.zhipu_api_key = settings.ZHIPU_API_KEY
        self.zhipu_model = settings.ZHIPU_MODEL

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Send chat request to AI model

        Args:
            messages: Message history
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Max tokens

        Returns:
            AI response text
        """
        if self.provider == "openai":
            return await self._chat_openai(messages, system_prompt, temperature, max_tokens)
        elif self.provider == "zhipu":
            return await self._chat_zhipu(messages, system_prompt, temperature, max_tokens)
        else:
            raise AIException(f"Unknown AI provider: {self.provider}")

    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI GPT-4 chat"""
        try:
            import aiohttp

            # Build messages
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            payload = {
                "model": self.openai_model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.openai_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise AIException(f"OpenAI API error: {error_text}")

                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]

        except AIException:
            raise
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise AIException(f"OpenAI chat failed: {str(e)}")

    async def _chat_zhipu(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Zhipu GLM-4 chat"""
        try:
            import aiohttp

            # Build messages
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            payload = {
                "model": self.zhipu_model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            headers = {
                "Authorization": f"Bearer {self.zhipu_api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise AIException(f"Zhipu API error: {error_text}")

                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]

        except AIException:
            raise
        except Exception as e:
            logger.error(f"Zhipu chat error: {e}")
            raise AIException(f"Zhipu chat failed: {str(e)}")

    async def analyze_video(
        self,
        video_title: str,
        video_script: str,
        keyframes: List[str],
        analysis_type: str
    ) -> Dict[str, Any]:
        """
        Analyze video content

        Args:
            video_title: Video title
            video_script: Video script (ASR text)
            keyframes: List of keyframe image paths
            analysis_type: Type of analysis

        Returns:
            Analysis result
        """
        prompt = self._build_analysis_prompt(analysis_type)
        messages = [
            {"role": "user", "content": f"视频标题: {video_title}\n\n视频脚本:\n{video_script}"}
        ]

        response = await self.chat(messages, system_prompt=prompt)
        return self._parse_analysis_response(response, analysis_type)

    def _build_analysis_prompt(self, analysis_type: str) -> str:
        """Build analysis prompt based on type"""
        prompts = {
            "golden_3_seconds": """你是一位短视频营销专家。你的任务是从视频脚本中提取"黄金3秒"开场文案。

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
}""",

            "script_structure": """你是一位内容结构分析师。你的任务是分析短视频的脚本结构。

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
}""",

            "sentiment": """你是一位情感分析专家。你的任务是分析评论区用户评论的情感倾向。

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
}""",

            "comprehensive": """你是一位短视频爆款分析师。你的任务是全面分析短视频的爆款潜力。

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
        }
        return prompts.get(analysis_type, prompts["comprehensive"])

    def _parse_analysis_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse AI response to structured data"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {"raw_response": response}
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return {"raw_response": response}


ai_service = AIService()
