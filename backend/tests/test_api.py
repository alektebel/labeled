"""
Tests for FastAPI backend endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app, get_current_user
from labeled_platform.database import Base, get_db, User, DataItem, Label


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Set up test database before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestAuthentication:
    """Test authentication endpoints."""

    def test_register_user(self):
        """Test user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "wallet_address" in data
        assert data["token_balance"] >= 0

    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "testpass123"
            }
        )

        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "testpass123"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_login_success(self):
        """Test successful login."""
        # Register user
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        # Login
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpass"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self):
        """Test getting current user info."""
        # Register and login
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        token = login_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestDataItems:
    """Test data item endpoints."""

    def get_auth_token(self):
        """Helper to get auth token."""
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        return response.json()["access_token"]

    def test_create_data_item(self):
        """Test creating a data item."""
        token = self.get_auth_token()

        response = client.post(
            "/data-items",
            json={
                "external_id": "item1",
                "item_type": "image",
                "data_url": "https://example.com/image.jpg",
                "required_labels": 5
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "item1"
        assert data["item_type"] == "image"
        assert data["required_labels"] == 5

    def test_list_data_items(self):
        """Test listing data items."""
        token = self.get_auth_token()

        # Create some items
        for i in range(3):
            client.post(
                "/data-items",
                json={
                    "external_id": f"item{i}",
                    "item_type": "image",
                    "data_url": f"https://example.com/image{i}.jpg"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

        # List items
        response = client.get(
            "/data-items",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_data_item(self):
        """Test getting a specific data item."""
        token = self.get_auth_token()

        # Create item
        create_response = client.post(
            "/data-items",
            json={
                "external_id": "item1",
                "item_type": "image",
                "data_url": "https://example.com/image.jpg"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        item_id = create_response.json()["id"]

        # Get item
        response = client.get(
            f"/data-items/{item_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["external_id"] == "item1"


class TestLabels:
    """Test label submission and consensus."""

    def create_test_user(self, username, email):
        """Helper to create and login user."""
        client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "testpass123"
            }
        )

        response = client.post(
            "/auth/login",
            json={
                "username": username,
                "password": "testpass123"
            }
        )

        return response.json()["access_token"]

    def test_submit_label(self):
        """Test submitting a label."""
        token = self.create_test_user("user1", "user1@example.com")

        # Create data item
        item_response = client.post(
            "/data-items",
            json={
                "external_id": "item1",
                "item_type": "image",
                "data_url": "https://example.com/image.jpg",
                "required_labels": 3
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        item_id = item_response.json()["id"]

        # Submit label
        response = client.post(
            "/labels",
            json={
                "data_item_id": item_id,
                "label_value": "cat",
                "confidence": 1.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["label"]["label_value"] == "cat"

    def test_duplicate_label_rejected(self):
        """Test that duplicate labels are rejected."""
        token = self.create_test_user("user1", "user1@example.com")

        # Create data item
        item_response = client.post(
            "/data-items",
            json={
                "external_id": "item1",
                "item_type": "image",
                "data_url": "https://example.com/image.jpg"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        item_id = item_response.json()["id"]

        # Submit first label
        client.post(
            "/labels",
            json={
                "data_item_id": item_id,
                "label_value": "cat"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to submit second label for same item
        response = client.post(
            "/labels",
            json={
                "data_item_id": item_id,
                "label_value": "dog"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400


class TestTokens:
    """Test token-related endpoints."""

    def get_auth_token(self):
        """Helper to get auth token."""
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        return response.json()["access_token"]

    def test_get_token_balance(self):
        """Test getting token balance."""
        token = self.get_auth_token()

        response = client.get(
            "/tokens/balance",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "balance" in response.json()

    def test_get_token_stats(self):
        """Test getting token statistics."""
        token = self.get_auth_token()

        response = client.get(
            "/tokens/stats",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "total_rewards" in data
        assert "total_penalties" in data

    def test_get_leaderboard(self):
        """Test getting token leaderboard."""
        token = self.get_auth_token()

        response = client.get(
            "/tokens/leaderboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestBlockchainEndpoints:
    """Test blockchain information endpoints."""

    def test_get_blockchain_info(self):
        """Test getting blockchain info."""
        response = client.get("/blockchain/info")

        assert response.status_code == 200
        data = response.json()
        assert "total_blocks" in data
        assert "difficulty" in data
        assert "is_valid" in data

    def test_get_blocks(self):
        """Test getting recent blocks."""
        response = client.get("/blockchain/blocks")

        assert response.status_code == 200
        blocks = response.json()
        assert isinstance(blocks, list)
        assert len(blocks) >= 1  # At least genesis block


class TestPlatformStats:
    """Test platform statistics."""

    def test_get_platform_stats(self):
        """Test getting platform statistics."""
        # Create a user first
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        token = response.json()["access_token"]

        response = client.get(
            "/stats/platform",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "data_items" in data
        assert "total_labels" in data
        assert "blockchain" in data
