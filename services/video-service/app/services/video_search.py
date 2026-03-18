"""
Video Search Service - Similar Video Retrieval
Uses Elasticsearch with vector search
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.services.embedding import embedding_service


# Elasticsearch index name
VIDEOS_INDEX = "videos"


class VideoSearchService:
    """视频检索服务"""

    def __init__(self, es_client=None):
        self.es_client = es_client

    async def create_index(self) -> bool:
        """创建视频索引"""
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")

        # 检查索引是否存在
        if await self.es_client.index_exists(VIDEOS_INDEX):
            logger.info(f"Index {VIDEOS_INDEX} already exists")
            return False

        # 创建索引映射
        mappings = {
            "properties": {
                "video_id": {"type": "keyword"},
                "platform": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "ik_max_word"},
                "description": {"type": "text", "analyzer": "ik_max_word"},
                "asr_text": {"type": "text", "analyzer": "ik_max_word"},
                "ocr_text": {"type": "text", "analyzer": "ik_max_word"},
                "tags": {"type": "keyword"},
                "category": {"type": "keyword"},
                "creator_id": {"type": "keyword"},
                "play_count": {"type": "long"},
                "like_count": {"type": "long"},
                "comment_count": {"type": "long"},
                "duration": {"type": "integer"},
                "publish_time": {"type": "date"},
                "vector": {
                    "type": "dense_vector",
                    "dims": 1536,
                    "index": True,
                    "similarity": "cosine"
                },
                "frame_vectors": {
                    "type": "dense_vector",
                    "dims": 1536,
                    "index": True,
                    "similarity": "cosine"
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }

        await self.es_client.create_index(VIDEOS_INDEX, mappings=mappings)
        return True

    async def index_video(
        self,
        video_id: str,
        video_data: Dict[str, Any],
        vector: Optional[List[float]] = None,
        frame_vectors: Optional[List[List[float]]] = None
    ) -> str:
        """
        索引视频

        Args:
            video_id: 视频ID
            video_data: 视频数据
            vector: 视频向量
            frame_vectors: 帧向量列表

        Returns:
            文档ID
        """
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")

        # 准备文档
        doc = {
            "video_id": video_id,
            "platform": video_data.get("platform"),
            "title": video_data.get("title", ""),
            "description": video_data.get("description", ""),
            "asr_text": video_data.get("asr_text", ""),
            "ocr_text": video_data.get("ocr_text", ""),
            "tags": video_data.get("tags", []),
            "category": video_data.get("category"),
            "creator_id": video_data.get("creator_id"),
            "play_count": video_data.get("play_count", 0),
            "like_count": video_data.get("like_count", 0),
            "comment_count": video_data.get("comment_count", 0),
            "duration": video_data.get("duration", 0),
            "publish_time": video_data.get("publish_time"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # 添加向量
        if vector:
            doc["vector"] = vector

        if frame_vectors:
            # 取第一帧向量作为代表
            doc["frame_vectors"] = frame_vectors[0] if frame_vectors else None

        # 索引文档
        doc_id = await self.es_client.index_document(
            index=VIDEOS_INDEX,
            document=doc,
            doc_id=video_id
        )

        logger.info(f"Video indexed: {video_id}")
        return doc_id

    async def search_by_text(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        文本搜索

        Args:
            query: 搜索文本
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            搜索结果
        """
        # 搜索多个字段
        must = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "description", "asr_text", "ocr_text", "tags"],
                    "type": "best_fields"
                }
            }
        ]

        # 添加过滤条件
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if value is not None:
                    filter_clauses.append({"term": {key: value}})

            if filter_clauses:
                must.append({"bool": {"filter": filter_clauses}})

        query_body = {
            "query": {
                "bool": {
                    "must": must
                }
            },
            "from": (page - 1) * page_size,
            "size": page_size,
            "sort": [
                {"_score": "desc"},
                {"play_count": "desc"}
            ]
        }

        result = await self.es_client.search(VIDEOS_INDEX, query_body)

        return {
            "total": result["total"],
            "hits": result["hits"],
            "page": page,
            "page_size": page_size
        }

    async def search_by_vector(
        self,
        vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10,
        vector_field: str = "vector"
    ) -> Dict[str, Any]:
        """
        向量相似度搜索

        Args:
            vector: 查询向量
            filters: 过滤条件
            page: 页码
            page_size: 每页数量
            vector_field: 向量字段名

        Returns:
            搜索结果
        """
        # 构建查询
        must = [
            {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, '{vector_field}') + 1.0",
                        "params": {"query_vector": vector}
                    }
                }
            }
        ]

        # 添加过滤条件
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if value is not None:
                    filter_clauses.append({"term": {key: value}})

            if filter_clauses:
                must.append({"bool": {"filter": filter_clauses}})

        query_body = {
            "query": {
                "bool": {
                    "must": must
                }
            },
            "from": (page - 1) * page_size,
            "size": page_size
        }

        result = await self.es_client.search(VIDEOS_INDEX, query_body)

        return {
            "total": result["total"],
            "hits": result["hits"],
            "page": page,
            "page_size": page_size
        }

    async def search_similar(
        self,
        video_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        查找相似视频

        Args:
            video_id: 参考视频ID
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            相似视频列表
        """
        # 获取参考视频的向量
        video_doc = await self.es_client.get_document(VIDEOS_INDEX, video_id)

        if not video_doc:
            raise ValueError(f"Video {video_id} not found")

        vector = video_doc.get("vector")
        if not vector:
            # 如果没有向量，使用帧向量
            vector = video_doc.get("frame_vectors")

        if not vector:
            raise ValueError(f"No vector found for video {video_id}")

        return await self.search_by_vector(vector, filters, page, page_size)

    async def search_by_image(
        self,
        image_path: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        通过图片搜索相似视频

        Args:
            image_path: 图片路径
            filters: 过滤条件
            page: 页码
            page_size: 每页数量

        Returns:
            搜索结果
        """
        # 向量化图片
        vector = await embedding_service.embed_video_frame(image_path)

        return await self.search_by_vector(vector, filters, page, page_size)

    async def delete_video(self, video_id: str) -> bool:
        """删除视频索引"""
        if not self.es_client:
            raise ValueError("Elasticsearch client not initialized")

        return await self.es_client.delete_document(VIDEOS_INDEX, video_id)


video_search_service = VideoSearchService()
