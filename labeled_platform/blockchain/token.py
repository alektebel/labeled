"""
LABD Token - Labeling Data Token.

Token system for rewarding accurate labelers and penalizing inaccurate ones.
"""

from typing import Dict, List, Optional
from .blockchain import Blockchain, Transaction
import time


class LABDToken:
    """
    LABD Token management system.

    Features:
    - Mint tokens for new users
    - Reward accurate labelers
    - Penalize inaccurate labelers
    - Transfer tokens between users
    """

    def __init__(
        self,
        blockchain: Optional[Blockchain] = None,
        initial_balance: float = 100.0,
        reward_amount: float = 10.0,
        penalty_amount: float = 5.0
    ):
        """
        Initialize LABD token system.

        Args:
            blockchain: Existing blockchain (creates new if None)
            initial_balance: Starting balance for new users
            reward_amount: Tokens awarded for correct labels
            penalty_amount: Tokens deducted for incorrect labels
        """
        self.blockchain = blockchain or Blockchain(difficulty=2)
        self.initial_balance = initial_balance
        self.reward_amount = reward_amount
        self.penalty_amount = penalty_amount

    def mint_tokens(self, address: str, amount: Optional[float] = None) -> bool:
        """
        Mint new tokens for a user (initial allocation).

        Args:
            address: User address
            amount: Amount to mint (uses initial_balance if None)

        Returns:
            True if successful
        """
        amount = amount or self.initial_balance

        transaction = Transaction(
            sender="SYSTEM",
            recipient=address,
            amount=amount,
            transaction_type="mint",
            metadata={"reason": "initial_allocation"}
        )

        return self.blockchain.add_transaction(transaction)

    def reward_labeler(
        self,
        address: str,
        label_id: str,
        amount: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Reward a labeler for accurate labeling.

        Args:
            address: Labeler address
            label_id: ID of the label
            amount: Reward amount (uses default if None)
            metadata: Additional metadata

        Returns:
            True if successful
        """
        amount = amount or self.reward_amount
        meta = metadata or {}
        meta["label_id"] = label_id

        transaction = Transaction(
            sender="SYSTEM",
            recipient=address,
            amount=amount,
            transaction_type="reward",
            metadata=meta
        )

        return self.blockchain.add_transaction(transaction)

    def penalize_labeler(
        self,
        address: str,
        label_id: str,
        amount: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Penalize a labeler for inaccurate labeling.

        Args:
            address: Labeler address
            label_id: ID of the label
            amount: Penalty amount (uses default if None)
            metadata: Additional metadata

        Returns:
            True if successful
        """
        amount = amount or self.penalty_amount
        meta = metadata or {}
        meta["label_id"] = label_id

        # Check if user has sufficient balance
        current_balance = self.blockchain.get_balance(address)
        if current_balance < amount:
            # Penalize with remaining balance if insufficient
            amount = max(0, current_balance)

        if amount <= 0:
            return False

        transaction = Transaction(
            sender=address,
            recipient="SYSTEM",
            amount=amount,
            transaction_type="penalty",
            metadata=meta
        )

        return self.blockchain.add_transaction(transaction)

    def transfer(self, sender: str, recipient: str, amount: float) -> bool:
        """
        Transfer tokens between users.

        Args:
            sender: Sender address
            recipient: Recipient address
            amount: Amount to transfer

        Returns:
            True if successful
        """
        transaction = Transaction(
            sender=sender,
            recipient=recipient,
            amount=amount,
            transaction_type="transfer"
        )

        return self.blockchain.add_transaction(transaction)

    def get_balance(self, address: str) -> float:
        """Get token balance for an address."""
        return self.blockchain.get_balance(address)

    def get_transaction_history(self, address: str) -> List[Transaction]:
        """Get transaction history for an address."""
        return self.blockchain.get_transaction_history(address)

    def mine_block(self, miner_address: str = "SYSTEM"):
        """Mine pending transactions into a new block."""
        return self.blockchain.mine_pending_transactions(miner_address)

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, any]]:
        """
        Get top token holders.

        Args:
            limit: Number of top holders to return

        Returns:
            List of {address, balance, rank} sorted by balance
        """
        # Get all unique addresses
        addresses = set()
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.sender != "SYSTEM":
                    addresses.add(tx.sender)
                if tx.recipient != "SYSTEM":
                    addresses.add(tx.recipient)

        # Calculate balances and sort
        balances = [(addr, self.get_balance(addr)) for addr in addresses]
        balances.sort(key=lambda x: x[1], reverse=True)

        # Format leaderboard
        leaderboard = []
        for rank, (address, balance) in enumerate(balances[:limit], 1):
            leaderboard.append({
                "rank": rank,
                "address": address,
                "balance": balance
            })

        return leaderboard

    def get_stats(self, address: Optional[str] = None) -> Dict:
        """
        Get statistics about tokens and transactions.

        Args:
            address: Specific address (None for global stats)

        Returns:
            Dictionary with statistics
        """
        if address:
            transactions = self.get_transaction_history(address)
            rewards = sum(tx.amount for tx in transactions
                         if tx.transaction_type == "reward" and tx.recipient == address)
            penalties = sum(tx.amount for tx in transactions
                          if tx.transaction_type == "penalty" and tx.sender == address)

            return {
                "address": address,
                "balance": self.get_balance(address),
                "total_transactions": len(transactions),
                "total_rewards": rewards,
                "total_penalties": penalties,
                "net_earnings": rewards - penalties
            }
        else:
            # Global stats
            total_supply = sum(self.blockchain.balances.values())
            total_transactions = sum(len(block.transactions) for block in self.blockchain.chain)

            return {
                "total_supply": total_supply,
                "total_blocks": len(self.blockchain.chain),
                "total_transactions": total_transactions,
                "pending_transactions": len(self.blockchain.pending_transactions),
                "difficulty": self.blockchain.difficulty
            }
