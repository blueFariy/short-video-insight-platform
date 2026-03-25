"""
Collection Schemas
"""
from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============ Request Schemas ============

class CollectionCreateRequest(BaseModel):
    """创建收藏请求"""
    item_type: str = Field(..., description="收藏类型: video, script, insight, creator")
    item_id: Union[int, str] = Field(..., description="收藏项ID (支持数字或字符串如B站BV号)")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")
    folder: Optional[str] = Field(None, max_length=100, description="收藏夹")

    @field_validator('item_id', mode='before')
    @classmethod
    def convert_item_id_to_string(cls, v):
        """确保item_id始终转换为字符串"""
        return str(v) if v is not None else v


class CollectionUpdateRequest(BaseModel):
    """更新收藏请求"""
    item_type: Optional[str] = Field(None, description="收藏类型: video, script, insight, creator")
    item_id: Optional[Union[int, str]] = Field(None, description="收藏项ID")
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")
    folder: Optional[str] = Field(None, max_length=100, description="收藏夹")
    is_analysis: Optional[bool] = Field(None, description="是否已分析")

    @field_validator('item_id', mode='before')
    @classmethod
    def convert_item_id_to_string(cls, v):
        """确保item_id始终转换为字符串"""
        return str(v) if v is not None else v


class CollectionBatchDeleteRequest(BaseModel):
    """批量删除收藏请求"""
    ids: List[int] = Field(..., description="收藏ID列表")


class CollectionMoveRequest(BaseModel):
    """移动收藏到文件夹请求"""
    ids: List[int] = Field(..., description="收藏ID列表")
    folder: str = Field(..., max_length=100, description="目标文件夹")


# ============ Response Schemas ============

class CollectionResponse(BaseModel):
    """收藏响应"""
    id: int
    user_id: int
    item_type: str
    item_id: Union[int, str]
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    is_analysis: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionDetailResponse(BaseModel):
    """收藏详情响应（包含关联的详细信息）"""
    id: int
    user_id: int
    item_type: str
    item_id: Union[int, str]
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    is_analysis: bool
    created_at: datetime
    # 关联信息
    video_info: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionListResponse(BaseModel):
    """收藏列表响应"""
    id: int
    item_type: str
    item_id: Union[int, str]
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    is_analysis: bool
    created_at: datetime
    # 关联的视频信息
    video_info: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class FolderInfoResponse(BaseModel):
    """文件夹信息响应"""
    name: str
    count: int


class CollectionStatsResponse(BaseModel):
    """收藏统计响应"""
    total: int
    by_type: dict
    by_folder: List[FolderInfoResponse]
    favorites: int
