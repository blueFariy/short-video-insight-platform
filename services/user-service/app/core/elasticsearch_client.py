"""
Elasticsearch Connection
"""
from typing import Any, Optional
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

        # 创建客户端
        self._client = AsyncElasticsearch(
            [url],
            verify_certs=False,
            retry_on_timeout=True,
            max_retries=3
        )

        # 测试连接
        await self._client.ping()
        logger.info("Elasticsearch connected successfully")

    async def close(self) -> None:
        """关闭Elasticsearch连接"""
        if self._client:
            await self._client.close()
        logger.info("Elasticsearch connection closed")

    @property
    def client(self) -> AsyncElasticsearch:
        """获取客户端"""
        if not self._client:
            raise RuntimeError("Elasticsearch not initialized. Call init_elasticsearch() first.")
        return self._client

    # 索引操作
    async def create_index(
        self,
        index: str,
        mappings: Optional[dict] = None,
        settings: Optional[dict] = None
    ) -> bool:
        """创建索引"""
        body = {}
        if mappings:
            body["mappings"] = mappings
        if settings:
            body["settings"] = settings

        exists = await self._client.indices.exists(index=index)
        if exists:
            logger.info(f"Index {index} already exists")
            return False

        await self._client.indices.create(index=index, body=body)
        logger.info(f"Index {index} created")
        return True

    async def delete_index(self, index: str) -> bool:
        """删除索引"""
        exists = await self._client.indices.exists(index=index)
        if not exists:
            logger.info(f"Index {index} does not exist")
            return False

        await self._client.indices.delete(index=index)
        logger.info(f"Index {index} deleted")
        return True

    async def index_exists(self, index: str) -> bool:
        """检查索引是否存在"""
        return await self._client.indices.exists(index=index)

    # 文档操作
    async def index_document(
        self,
        index: str,
        document: dict,
        doc_id: Optional[str] = None
    ) -> str:
        """索引文档"""
        result = await self._client.index(
            index=index,
            document=document,
            id=doc_id
        )
        return result["_id"]

    async def get_document(self, index: str, doc_id: str) -> Optional[dict]:
        """获取文档"""
        try:
            result = await self._client.get(index=index, id=doc_id)
            return result["_source"]
        except Exception:
            return None

    async def update_document(
        self,
        index: str,
        doc_id: str,
        document: dict
    ) -> bool:
        """更新文档"""
        try:
            await self._client.update(
                index=index,
                id=doc_id,
                doc=document
            )
            return True
        except Exception:
            return False

    async def delete_document(self, index: str, doc_id: str) -> bool:
        """删除文档"""
        try:
            await self._client.delete(index=index, id=doc_id)
            return True
        except Exception:
            return False

    # 搜索操作
    async def search(
        self,
        index: str,
        query: dict,
        from_: int = 0,
        size: int = 10,
        sort: Optional[list] = None
    ) -> dict:
        """搜索"""
        body = {
            "query": query,
            "from": from_,
            "size": size
        }
        if sort:
            body["sort"] = sort

        result = await self._client.search(index=index, body=body)
        return {
            "total": result["hits"]["total"]["value"],
            "hits": [hit["_source"] for hit in result["hits"]["hits"]],
            "took": result["took"]
        }

    async def scroll_search(
        self,
        index: str,
        query: dict,
        scroll: str = "5m",
        size: int = 1000
    ) -> list:
        """滚动搜索（用于大量数据）"""
        body = {
            "query": query,
            "size": size,
            "scroll": scroll
        }

        results = []
        response = await self._client.search(index=index, body=body, scroll=scroll)
        scroll_id = response["_scroll_id"]
        results.extend([hit["_source"] for hit in response["hits"]["hits"]])

        while len(response["hits"]["hits"]) > 0:
            response = await self._client.scroll(
                scroll_id=scroll_id,
                scroll=scroll
            )
            results.extend([hit["_source"] for hit in response["hits"]["hits"]])

        # 清理scroll
        await self._client.clear_scroll(scroll_id=scroll_id)

        return results


# 全局Elasticsearch管理器实例
es_manager = ElasticsearchManager()


# 依赖注入函数
async def get_elasticsearch() -> AsyncElasticsearch:
    """FastAPI依赖注入 - 获取Elasticsearch客户端"""
    return es_manager.client
