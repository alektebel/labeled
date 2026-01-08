"""
FastAPI backend for the Labeled platform.

Features:
- User authentication and registration
- Data item management
- Label submission
- Consensus computation
- LABD token integration
- Blockchain operations
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta
import os

from labeled_platform.database import get_db, User, DataItem, Label, LabelingSession, init_db
from labeled_platform.blockchain import LABDToken
from labeled.consensus import BFTConsensus

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Initialize FastAPI
app = FastAPI(
    title="Labeled Platform API",
    description="Decentralized data labeling platform with BFT consensus and LABD tokens",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global instances
token_system = LABDToken()
consensus_system = BFTConsensus()


# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    wallet_address: str
    total_labels: int
    accuracy: float
    reputation_score: float
    token_balance: float

    class Config:
        from_attributes = True


class DataItemCreate(BaseModel):
    external_id: str
    item_type: str
    data_url: str
    required_labels: int = 5
    metadata: dict = {}


class LabelSubmit(BaseModel):
    data_item_id: int
    label_value: str
    confidence: float = 1.0
    time_spent: Optional[float] = None


class TokenStats(BaseModel):
    balance: float
    total_rewards: float
    total_penalties: float
    net_earnings: float


# Authentication helpers
def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


# API Endpoints

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=User.hash_password(user_data.password),
        wallet_address=User.generate_wallet_address()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Mint initial tokens
    token_system.mint_tokens(user.wallet_address)
    token_system.mine_block()

    # Get token balance
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        wallet_address=user.wallet_address,
        total_labels=user.total_labels,
        accuracy=user.accuracy,
        reputation_score=user.reputation_score,
        token_balance=token_system.get_balance(user.wallet_address)
    )

    return user_response


@app.post("/auth/login")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user."""
    user = db.query(User).filter(User.username == credentials.username).first()

    if not user or not user.verify_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create access token
    access_token = create_access_token({"sub": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "wallet_address": user.wallet_address
        }
    }


@app.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        wallet_address=current_user.wallet_address,
        total_labels=current_user.total_labels,
        accuracy=current_user.accuracy,
        reputation_score=current_user.reputation_score,
        token_balance=token_system.get_balance(current_user.wallet_address)
    )


# Data item endpoints
@app.post("/data-items")
async def create_data_item(
    item: DataItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new data item."""
    # Check if already exists
    existing = db.query(DataItem).filter(DataItem.external_id == item.external_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Data item already exists")

    data_item = DataItem(
        external_id=item.external_id,
        item_type=item.item_type,
        data_url=item.data_url,
        required_labels=item.required_labels,
        metadata=item.metadata
    )

    db.add(data_item)
    db.commit()
    db.refresh(data_item)

    return data_item


@app.get("/data-items")
async def list_data_items(
    skip: int = 0,
    limit: int = 100,
    unlabeled_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List data items."""
    query = db.query(DataItem)

    if unlabeled_only:
        # Items the current user hasn't labeled yet
        labeled_ids = db.query(Label.data_item_id).filter(
            Label.user_id == current_user.id
        ).subquery()
        query = query.filter(~DataItem.id.in_(labeled_ids))

    items = query.offset(skip).limit(limit).all()
    return items


@app.get("/data-items/{item_id}")
async def get_data_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific data item."""
    item = db.query(DataItem).filter(DataItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Data item not found")
    return item


# Label submission
@app.post("/labels")
async def submit_label(
    label_data: LabelSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a label for a data item."""
    # Check if data item exists
    data_item = db.query(DataItem).filter(DataItem.id == label_data.data_item_id).first()
    if not data_item:
        raise HTTPException(status_code=404, detail="Data item not found")

    # Check if user already labeled this item
    existing_label = db.query(Label).filter(
        Label.user_id == current_user.id,
        Label.data_item_id == label_data.data_item_id
    ).first()

    if existing_label:
        raise HTTPException(status_code=400, detail="Already labeled this item")

    # Create label
    label = Label(
        user_id=current_user.id,
        data_item_id=label_data.data_item_id,
        label_value=label_data.label_value,
        confidence=label_data.confidence,
        time_spent=label_data.time_spent
    )

    db.add(label)
    db.commit()
    db.refresh(label)

    # Check if we have enough labels for consensus
    all_labels = db.query(Label).filter(Label.data_item_id == data_item.id).all()

    if len(all_labels) >= data_item.required_labels:
        # Compute consensus
        label_values = [l.label_value for l in all_labels]
        consensus_result = consensus_system.compute_consensus(label_values)

        if consensus_result.has_consensus:
            # Update data item with consensus
            data_item.consensus_label = consensus_result.consensus_label
            data_item.consensus_confidence = consensus_result.confidence
            data_item.has_consensus = True
            db.commit()

            # Reward/penalize labelers
            for lbl in all_labels:
                if not lbl.is_validated:
                    is_correct = lbl.label_value == consensus_result.consensus_label
                    lbl.is_validated = True
                    lbl.is_correct = is_correct

                    # Get user
                    user = db.query(User).filter(User.id == lbl.user_id).first()

                    if is_correct:
                        # Reward
                        token_system.reward_labeler(
                            user.wallet_address,
                            str(lbl.id),
                            metadata={"data_item_id": data_item.id}
                        )
                        lbl.reward_amount = token_system.reward_amount
                        user.update_stats(True)
                    else:
                        # Penalize
                        token_system.penalize_labeler(
                            user.wallet_address,
                            str(lbl.id),
                            metadata={"data_item_id": data_item.id}
                        )
                        lbl.penalty_amount = token_system.penalty_amount
                        user.update_stats(False)

            # Mine block with all transactions
            token_system.mine_block()
            db.commit()

    return {
        "label": label,
        "consensus_reached": data_item.has_consensus,
        "consensus_label": data_item.consensus_label
    }


# Token endpoints
@app.get("/tokens/balance")
async def get_token_balance(
    current_user: User = Depends(get_current_user)
):
    """Get user's token balance."""
    balance = token_system.get_balance(current_user.wallet_address)
    return {"balance": balance}


@app.get("/tokens/stats", response_model=TokenStats)
async def get_token_stats(
    current_user: User = Depends(get_current_user)
):
    """Get user's token statistics."""
    stats = token_system.get_stats(current_user.wallet_address)
    return TokenStats(**stats)


@app.get("/tokens/leaderboard")
async def get_leaderboard(limit: int = 10):
    """Get token leaderboard."""
    return token_system.get_leaderboard(limit)


@app.get("/tokens/history")
async def get_transaction_history(
    current_user: User = Depends(get_current_user)
):
    """Get user's transaction history."""
    transactions = token_system.get_transaction_history(current_user.wallet_address)
    return [tx.to_dict() for tx in transactions]


# Blockchain endpoints
@app.get("/blockchain/info")
async def get_blockchain_info():
    """Get blockchain information."""
    return {
        "total_blocks": len(token_system.blockchain.chain),
        "difficulty": token_system.blockchain.difficulty,
        "pending_transactions": len(token_system.blockchain.pending_transactions),
        "is_valid": token_system.blockchain.is_chain_valid()
    }


@app.get("/blockchain/blocks")
async def get_blocks(limit: int = 10):
    """Get recent blocks."""
    blocks = token_system.blockchain.chain[-limit:]
    return [block.to_dict() for block in blocks]


# Stats endpoints
@app.get("/stats/platform")
async def get_platform_stats(db: Session = Depends(get_db)):
    """Get platform statistics."""
    total_users = db.query(User).count()
    total_items = db.query(DataItem).count()
    total_labels = db.query(Label).count()
    items_with_consensus = db.query(DataItem).filter(DataItem.has_consensus == True).count()

    token_stats = token_system.get_stats()

    return {
        "users": total_users,
        "data_items": total_items,
        "total_labels": total_labels,
        "items_with_consensus": items_with_consensus,
        "blockchain": token_stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
