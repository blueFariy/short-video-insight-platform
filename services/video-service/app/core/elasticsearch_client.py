"""
Elasticsearch Connection
"""
from typing import Optional
from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.core.config import settings


class ElasticsearchManager:
    """Elasticsearch管理器"""

    def __init__(self):
        self._client: Optional[AsyncElasticsearch] = None

    async def init_elasticsearch(self, es_url: Optional[str] = None) -> None:
        """初始化Elasticsearch连接"""
        url = es_url or settings.ELASTICSEARCH_URL
        logger.info(f"Initializing Elasticsearch: {url}")

        self._client = AsyncElasticsearch(
            [url],
            verify_certs=False,
            retry_on_timeout=True,
            max_retries=3
        )

        await self._client.ping()
        logger.info("Elasticsearch connected successfully")

    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.close()
        logger.info("Elasticsearch connection closed")

    @property
    def client(self) -> AsyncElasticsearch:
        """获取客户端"""
        if not self._client:
            raise RuntimeError("Elasticsearch not initialized")
        return self._client

    async def create_index(self, index: str, mappings: Optional[dict] = None) -> bool:
        """创建索引"""
        exists = await self._client.indices.exists(index=index)
        if exists:
            return False
        body = {}
        if mappings:
            body["mappings"] = mappings
        await self._client.indices.create(index=index, body=body)
        return True

    async def index_exists(self, index: str) -> bool:
        """检查索引是否存在"""
        return await self._client.indices.exists(index=index)

    async def index_document(self, index: str, document: dict, doc_id: Optional[str] = None) -> str:
        """索引文档"""
        result = await self._client.index(index=index, document=document, id=doc_id)
        return result["_id"]

    async def get_document(self, index: str, doc_id: str) -> Optional[dict]:
        """获取文档"""
        try:
            result = await self._client.get(index=index, id=doc_id)
            return result["_source"]
        except Exception:
            return None

    async def delete_document(self, index: str, doc_id: str) -> bool:
        """删除文档"""
        try:
            await self._client.delete(index=index, id=doc_id)
            return True
        except Exception:
            return False

    async def search(self, index: str, query: dict, from_: int = 0, size: int = 10) -> dict:
        """搜索"""
        body = {"query": query, "from": from_, "size": size}
        result = await self._client.search(index=index, body=body)
        return {
            "total": result["hits"]["total"]["value"],
            "hits": [hit["_source"] for hit in result["hits"]["hits"]],
            "took": result["took"]
        }


es_manager = ElasticsearchManager()
