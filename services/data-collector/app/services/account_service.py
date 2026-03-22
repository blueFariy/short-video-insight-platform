"""
Account Management Service - Using PostgreSQL Database
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_manager, MonitoredAccount


class Account:
    """Competitor account model (for API compatibility)"""

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

    @classmethod
    def from_db_model(cls, db_account: MonitoredAccount) -> "Account":
        """Create from database model"""
        return cls(
            id=db_account.id,
            name=db_account.name,
            platform=db_account.platform,
            account_id=db_account.account_id,
            url=db_account.url,
            category=db_account.category,
            status=db_account.status,
            last_collection_time=db_account.last_collection_time,
            created_at=db_account.created_at
        )

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
    """Account management service using database"""

    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            try:
                db_manager.init_db()
                await db_manager.create_tables()
                self._initialized = True
                logger.info("Account service database initialized")
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}, using in-memory fallback")
                self._initialized = False

    async def _get_session(self) -> AsyncSession:
        """Get database session"""
        if not self._initialized:
            await self._ensure_initialized()
        # This returns a context manager
        return db_manager.get_session()

    async def create_account(
        self,
        name: str,
        platform: str,
        account_id: str,
        url: str,
        category: str = "general"
    ) -> Account:
        """Create a new account"""
        await self._ensure_initialized()

        account_id_gen = f"acc_{uuid.uuid4().hex[:8]}"

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    db_account = MonitoredAccount(
                        id=account_id_gen,
                        name=name,
                        platform=platform,
                        account_id=account_id,
                        url=url,
                        category=category,
                        status="active"
                    )
                    session.add(db_account)
                    await session.commit()
                    logger.info(f"Created account in database: {name}")
                    return Account(
                        id=account_id_gen,
                        name=name,
                        platform=platform,
                        account_id=account_id,
                        url=url,
                        category=category,
                        status="active"
                    )
            except Exception as e:
                logger.error(f"Failed to create account in database: {e}")

        # Fallback to in-memory
        return Account(
            id=account_id_gen,
            name=name,
            platform=platform,
            account_id=account_id,
            url=url,
            category=category,
            status="active"
        )

    async def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(MonitoredAccount).where(MonitoredAccount.id == account_id)
                    result = await session.execute(stmt)
                    db_account = result.scalar_one_or_none()
                    if db_account:
                        return Account.from_db_model(db_account)
            except Exception as e:
                logger.error(f"Failed to get account from database: {e}")

        return None

    async def list_accounts(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Account]:
        """List accounts with filters"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(MonitoredAccount)
                    conditions = []
                    if platform:
                        conditions.append(MonitoredAccount.platform == platform)
                    if category:
                        conditions.append(MonitoredAccount.category == category)
                    if status:
                        conditions.append(MonitoredAccount.status == status)

                    if conditions:
                        stmt = stmt.where(and_(*conditions))

                    result = await session.execute(stmt)
                    db_accounts = result.scalars().all()
                    return [Account.from_db_model(a) for a in db_accounts]
            except Exception as e:
                logger.error(f"Failed to list accounts from database: {e}")

        return []

    async def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Account]:
        """Update account"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(MonitoredAccount).where(MonitoredAccount.id == account_id)
                    result = await session.execute(stmt)
                    db_account = result.scalar_one_or_none()
                    if db_account:
                        if name:
                            db_account.name = name
                        if category:
                            db_account.category = category
                        if status:
                            db_account.status = status
                        db_account.updated_at = datetime.now()
                        await session.commit()
                        return Account.from_db_model(db_account)
            except Exception as e:
                logger.error(f"Failed to update account: {e}")

        return None

    async def delete_account(self, account_id: str) -> bool:
        """Delete account"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(MonitoredAccount).where(MonitoredAccount.id == account_id)
                    result = await session.execute(stmt)
                    db_account = result.scalar_one_or_none()
                    if db_account:
                        await session.delete(db_account)
                        await session.commit()
                        return True
            except Exception as e:
                logger.error(f"Failed to delete account: {e}")

        return False

    async def update_collection_time(self, account_id: str) -> bool:
        """Update last collection time"""
        await self._ensure_initialized()

        if self._initialized:
            try:
                async with db_manager.get_session() as session:
                    stmt = select(MonitoredAccount).where(MonitoredAccount.id == account_id)
                    result = await session.execute(stmt)
                    db_account = result.scalar_one_or_none()
                    if db_account:
                        db_account.last_collection_time = datetime.now()
                        await session.commit()
                        return True
            except Exception as e:
                logger.error(f"Failed to update collection time: {e}")

        return False

    async def get_active_accounts(self, platform: Optional[str] = None) -> List[Account]:
        """Get all active accounts"""
        return await self.list_accounts(platform=platform, status="active")


account_service = AccountService()
