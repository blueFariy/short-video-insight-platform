"""
User Service - Comprehensive Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Test core security functions
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


class TestSecurity:
    """Test security utilities"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "testuser", "user_id": "123"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_decode_access_token_valid(self):
        """Test JWT token decoding with valid token"""
        data = {"sub": "testuser", "user_id": "123"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == "123"

    def test_decode_access_token_invalid(self):
        """Test JWT token decoding with invalid token"""
        decoded = decode_access_token("invalid_token")
        assert decoded is None


class TestUserSchemas:
    """Test user schemas"""

    def test_user_create_valid(self):
        """Test UserCreate with valid data"""
        from app.schemas.user import UserCreate
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                password="password123"
            )

    def test_user_create_short_password(self):
        """Test UserCreate with short password"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="12345"
            )

    def test_user_login_valid(self):
        """Test UserLogin with valid data"""
        from app.schemas.user import UserLogin
        login = UserLogin(username="testuser", password="password123")
        assert login.username == "testuser"

    def test_password_change_valid(self):
        """Test PasswordChange with valid data"""
        from app.schemas.user import PasswordChange
        change = PasswordChange(
            old_password="oldpassword",
            new_password="newpassword123"
        )
        assert change.old_password == "oldpassword"
        assert change.new_password == "newpassword123"


class TestExceptions:
    """Test custom exceptions"""

    def test_app_exception(self):
        """Test AppException"""
        from app.core.exceptions import AppException
        exc = AppException("Test error", code=400)
        assert exc.message == "Test error"
        assert exc.code == 400

    def test_validation_exception(self):
        """Test ValidationException"""
        from app.core.exceptions import ValidationException
        exc = ValidationException("Invalid input")
        assert exc.code == 400

    def test_unauthorized_exception(self):
        """Test UnauthorizedException"""
        from app.core.exceptions import UnauthorizedException
        exc = UnauthorizedException()
        assert exc.code == 401


class TestResponseModel:
    """Test response models"""

    def test_success_response(self):
        """Test success response"""
        from app.core.response import success_response
        response = success_response(data={"key": "value"})
        assert response.code == 200
        assert response.message == "success"
        assert response.data == {"key": "value"}

    def test_error_response(self):
        """Test error response"""
        from app.core.response import error_response
        response = error_response(code=404, message="Not found")
        assert response.code == 404
        assert response.message == "Not found"


class TestCollectionSchemas:
    """Test collection schemas"""

    def test_collection_create_valid(self):
        """Test CollectionCreate with valid data"""
        from app.schemas.collection import CollectionCreate
        collection = CollectionCreate(
            title="Test Collection",
            type="video",
            content="Test content"
        )
        assert collection.title == "Test Collection"
        assert collection.type == "video"

    def test_collection_response(self):
        """Test CollectionResponse"""
        from app.schemas.collection import CollectionResponse
        now = datetime.now()
        collection = CollectionResponse(
            id="test_id",
            title="Test",
            type="video",
            content="Content",
            user_id="user_1",
            created_at=now,
            updated_at=now
        )
        assert collection.id == "test_id"
