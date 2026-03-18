"""
Schemas Package
"""
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserUpdateRequest,
    ChangePasswordRequest,
    UserPreferencesRequest,
    UserBaseResponse,
    UserResponse,
    UserListResponse,
    LoginResponse,
    TokenRefreshResponse,
    SubscriptionInfoResponse,
    SubscriptionUpgradeRequest
)
from app.schemas.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionBatchDeleteRequest,
    CollectionMoveRequest,
    CollectionResponse,
    CollectionDetailResponse,
    CollectionListResponse,
    FolderInfoResponse,
    CollectionStatsResponse
)

__all__ = [
    # User Schemas
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserUpdateRequest",
    "ChangePasswordRequest",
    "UserPreferencesRequest",
    "UserBaseResponse",
    "UserResponse",
    "UserListResponse",
    "LoginResponse",
    "TokenRefreshResponse",
    "SubscriptionInfoResponse",
    "SubscriptionUpgradeRequest",
    # Collection Schemas
    "CollectionCreateRequest",
    "CollectionUpdateRequest",
    "CollectionBatchDeleteRequest",
    "CollectionMoveRequest",
    "CollectionResponse",
    "CollectionDetailResponse",
    "CollectionListResponse",
    "FolderInfoResponse",
    "CollectionStatsResponse"
]
