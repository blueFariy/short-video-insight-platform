"""
Account Management Service
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class Account:
    """Competitor account model"""

    def __init__(
        self,
        id: str,
        name: str,
        platform: str,
        account_id: str,
        url: str,
        category: str = "general",
        status: str = "active",
        last_collection_time: Optional[datetime] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.platform = platform
        self.account_id = account_id
        self.url = url
        self.category = category
        self.status = status
        self.last_collection_time = last_collection_time
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "account_id": self.account_id,
            "url": self.url,
            "category": self.category,
            "status": self.status,
            "last_collection_time": self.last_collection_time.isoformat() if self.last_collection_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AccountService:
    """Account management service"""

    def __init__(self):
        # In-memory storage (replace with database in production)
        self.accounts: Dict[str, Account] = {}
        self._init_demo_accounts()

    def _init_demo_accounts(self):
        """Initialize demo accounts"""
        demo_accounts = [
            Account(
                id="acc_001",
                name="疯狂小杨哥",
                platform="douyin",
                account_id="xiaoyange",
                url="https://v.douyin.com/5j2Fkh/",
                category="搞笑",
                status="active"
            ),
            Account(
                id="acc_002",
                name="罗永浩",
                platform="douyin",
                account_id="laohu",
                url="https://v.douyin.com/5j3Gki/",
                category="科技",
                status="active"
            ),
            Account(
                id="acc_003",
                name="老高与小茉",
                platform="bilibili",
                account_id="BV1GJ411x7h7",
                url="https://space.bilibili.com/3368963",
                category="知识",
                status="active"
            ),
            Account(
                id="acc_004",
                name="李子柒",
                platform="xiaohongshu",
                account_id="Liziqi",
                url="https://www.xiaohongshu.com/user/profile/5a123456",
                category="生活",
                status="active"
            )
        ]
        for account in demo_accounts:
            self.accounts[account.id] = account

    async def create_account(
        self,
        name: str,
        platform: str,
        account_id: str,
        url: str,
        category: str = "general"
    ) -> Account:
        """Create a new account"""
        import uuid
        account = Account(
            id=f"acc_{uuid.uuid4().hex[:8]}",
            name=name,
            platform=platform,
            account_id=account_id,
            url=url,
            category=category,
            status="active"
        )
        self.accounts[account.id] = account
        logger.info(f"Created account: {account.name} ({account.platform})")
        return account

    async def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        return self.accounts.get(account_id)

    async def list_accounts(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Account]:
        """List accounts with filters"""
        results = list(self.accounts.values())

        if platform:
            results = [a for a in results if a.platform == platform]
        if category:
            results = [a for a in results if a.category == category]
        if status:
            results = [a for a in results if a.status == status]

        return results

    async def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Account]:
        """Update account"""
        account = self.accounts.get(account_id)
        if not account:
            return None

        if name:
            account.name = name
        if category:
            account.category = category
        if status:
            account.status = status

        return account

    async def delete_account(self, account_id: str) -> bool:
        """Delete account"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            return True
        return False

    async def update_collection_time(self, account_id: str) -> bool:
        """Update last collection time"""
        account = self.accounts.get(account_id)
        if account:
            account.last_collection_time = datetime.now()
            return True
        return False

    async def get_active_accounts(self, platform: Optional[str] = None) -> List[Account]:
        """Get all active accounts"""
        return await self.list_accounts(platform=platform, status="active")


account_service = AccountService()
