"""
Custom blockchain implementation for LABD token.

This blockchain provides a decentralized ledger for tracking LABD token
transactions with proof-of-work consensus.
"""

import hashlib
import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Transaction:
    """Represents a token transaction."""
    sender: str
    recipient: str
    amount: float
    timestamp: float = field(default_factory=time.time)
    transaction_type: str = "transfer"  # transfer, reward, penalty, mint
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert transaction to dictionary."""
        return asdict(self)

    def __hash__(self):
        """Make transaction hashable."""
        return hash(json.dumps(self.to_dict(), sort_keys=True))


@dataclass
class Block:
    """Represents a block in the blockchain."""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def calculate_hash(self) -> str:
        """Calculate the hash of this block."""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [t.to_dict() for t in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int = 4):
        """Mine the block using proof-of-work."""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self) -> Dict:
        """Convert block to dictionary."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [t.to_dict() for t in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    """
    A simple proof-of-work blockchain for LABD tokens.

    Features:
    - Proof-of-work mining
    - Transaction validation
    - Chain integrity verification
    - Pending transactions pool
    """

    def __init__(self, difficulty: int = 4, mining_reward: float = 10.0):
        """
        Initialize blockchain.

        Args:
            difficulty: Mining difficulty (number of leading zeros)
            mining_reward: Reward for mining a block
        """
        self.chain: List[Block] = [self._create_genesis_block()]
        self.difficulty = difficulty
        self.pending_transactions: List[Transaction] = []
        self.mining_reward = mining_reward
        self.balances: Dict[str, float] = {}

    def _create_genesis_block(self) -> Block:
        """Create the first block in the chain."""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0"
        )
        genesis_block.hash = genesis_block.calculate_hash()
        return genesis_block

    def get_latest_block(self) -> Block:
        """Get the most recent block."""
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the pending pool.

        Args:
            transaction: Transaction to add

        Returns:
            True if transaction is valid and added
        """
        # Validate transaction
        if not self._validate_transaction(transaction):
            return False

        self.pending_transactions.append(transaction)
        return True

    def _validate_transaction(self, transaction: Transaction) -> bool:
        """Validate a transaction."""
        # System transactions (mint, reward, penalty) are always valid
        if transaction.sender == "SYSTEM":
            return True

        # Check if sender has sufficient balance
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < transaction.amount:
            return False

        return transaction.amount > 0

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """
        Mine all pending transactions into a new block.

        Args:
            miner_address: Address to receive mining reward

        Returns:
            The newly mined block
        """
        # Add mining reward transaction
        reward_tx = Transaction(
            sender="SYSTEM",
            recipient=miner_address,
            amount=self.mining_reward,
            transaction_type="mining_reward"
        )

        # Create new block with all pending transactions
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions + [reward_tx],
            previous_hash=self.get_latest_block().hash
        )

        # Mine the block
        block.mine_block(self.difficulty)

        # Add to chain
        self.chain.append(block)

        # Update balances
        self._update_balances(block)

        # Clear pending transactions
        self.pending_transactions = []

        return block

    def _update_balances(self, block: Block):
        """Update balance cache from block transactions."""
        for tx in block.transactions:
            if tx.sender != "SYSTEM":
                self.balances[tx.sender] = self.balances.get(tx.sender, 0) - tx.amount
            self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount

    def get_balance(self, address: str) -> float:
        """
        Get the balance of an address.

        Args:
            address: User address

        Returns:
            Current balance
        """
        # Use cached balance if available
        if address in self.balances:
            return self.balances[address]

        # Calculate from chain
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount

        self.balances[address] = balance
        return balance

    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Verify hash
            if current_block.hash != current_block.calculate_hash():
                return False

            # Verify link to previous block
            if current_block.previous_hash != previous_block.hash:
                return False

            # Verify proof-of-work
            if not current_block.hash.startswith("0" * self.difficulty):
                return False

        return True

    def get_transaction_history(self, address: str) -> List[Transaction]:
        """Get all transactions for an address."""
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    transactions.append(tx)
        return transactions

    def to_dict(self) -> Dict:
        """Convert blockchain to dictionary."""
        return {
            "chain": [block.to_dict() for block in self.chain],
            "difficulty": self.difficulty,
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "mining_reward": self.mining_reward
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Blockchain":
        """Create blockchain from dictionary."""
        blockchain = cls(
            difficulty=data["difficulty"],
            mining_reward=data["mining_reward"]
        )

        # Reconstruct chain (skip genesis block)
        blockchain.chain = []
        for block_data in data["chain"]:
            transactions = [Transaction(**tx) for tx in block_data["transactions"]]
            block = Block(
                index=block_data["index"],
                timestamp=block_data["timestamp"],
                transactions=transactions,
                previous_hash=block_data["previous_hash"],
                nonce=block_data["nonce"],
                hash=block_data["hash"]
            )
            blockchain.chain.append(block)

        # Reconstruct pending transactions
        blockchain.pending_transactions = [
            Transaction(**tx) for tx in data["pending_transactions"]
        ]

        # Rebuild balance cache
        blockchain.balances = {}
        for block in blockchain.chain:
            blockchain._update_balances(block)

        return blockchain
