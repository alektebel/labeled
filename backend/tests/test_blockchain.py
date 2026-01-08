"""
Tests for blockchain and LABD token functionality.
"""

import pytest
from labeled_platform.blockchain import Blockchain, Block, Transaction, LABDToken


class TestBlockchain:
    """Test blockchain core functionality."""

    def test_genesis_block_creation(self):
        """Test genesis block is created correctly."""
        blockchain = Blockchain()
        assert len(blockchain.chain) == 1
        assert blockchain.chain[0].index == 0
        assert blockchain.chain[0].previous_hash == "0"

    def test_add_valid_transaction(self):
        """Test adding a valid transaction."""
        blockchain = Blockchain()
        tx = Transaction(sender="SYSTEM", recipient="user1", amount=100)

        assert blockchain.add_transaction(tx) is True
        assert len(blockchain.pending_transactions) == 1

    def test_reject_insufficient_balance(self):
        """Test rejecting transaction with insufficient balance."""
        blockchain = Blockchain()
        tx = Transaction(sender="user1", recipient="user2", amount=100)

        assert blockchain.add_transaction(tx) is False

    def test_mine_block(self):
        """Test mining a block."""
        blockchain = Blockchain(difficulty=2)
        tx = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain.add_transaction(tx)

        block = blockchain.mine_pending_transactions("miner1")

        assert len(blockchain.chain) == 2
        assert block.hash.startswith("00")
        assert len(blockchain.pending_transactions) == 0

    def test_chain_validation(self):
        """Test blockchain validation."""
        blockchain = Blockchain(difficulty=2)

        tx1 = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain.add_transaction(tx1)
        blockchain.mine_pending_transactions("miner1")

        tx2 = Transaction(sender="user1", recipient="user2", amount=50)
        blockchain.add_transaction(tx2)
        blockchain.mine_pending_transactions("miner1")

        assert blockchain.is_chain_valid() is True

    def test_tampered_chain_invalid(self):
        """Test that tampering invalidates chain."""
        blockchain = Blockchain(difficulty=2)

        tx = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain.add_transaction(tx)
        blockchain.mine_pending_transactions("miner1")

        # Tamper with block
        blockchain.chain[1].transactions[0].amount = 1000

        assert blockchain.is_chain_valid() is False

    def test_balance_calculation(self):
        """Test balance calculation."""
        blockchain = Blockchain()

        tx1 = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain.add_transaction(tx1)
        blockchain.mine_pending_transactions("miner1")

        assert blockchain.get_balance("user1") >= 100

        tx2 = Transaction(sender="user1", recipient="user2", amount=50)
        blockchain.add_transaction(tx2)
        blockchain.mine_pending_transactions("miner1")

        assert blockchain.get_balance("user1") >= 50
        assert blockchain.get_balance("user2") == 50

    def test_transaction_history(self):
        """Test transaction history retrieval."""
        blockchain = Blockchain()

        tx1 = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain.add_transaction(tx1)
        blockchain.mine_pending_transactions("miner1")

        history = blockchain.get_transaction_history("user1")
        assert len(history) >= 1
        assert any(tx.recipient == "user1" for tx in history)


class TestLABDToken:
    """Test LABD token functionality."""

    def test_mint_tokens(self):
        """Test minting tokens for new user."""
        token = LABDToken()
        assert token.mint_tokens("user1", 100) is True
        token.mine_block()

        assert token.get_balance("user1") == 100

    def test_reward_labeler(self):
        """Test rewarding a labeler."""
        token = LABDToken(reward_amount=10)
        token.mint_tokens("user1", 50)
        token.mine_block()

        assert token.reward_labeler("user1", "label123") is True
        token.mine_block()

        assert token.get_balance("user1") == 60

    def test_penalize_labeler(self):
        """Test penalizing a labeler."""
        token = LABDToken(penalty_amount=5)
        token.mint_tokens("user1", 50)
        token.mine_block()

        assert token.penalize_labeler("user1", "label123") is True
        token.mine_block()

        assert token.get_balance("user1") == 45

    def test_penalize_insufficient_balance(self):
        """Test penalizing with insufficient balance."""
        token = LABDToken(penalty_amount=100)
        token.mint_tokens("user1", 50)
        token.mine_block()

        # Should still work but only penalize available balance
        token.penalize_labeler("user1", "label123")
        token.mine_block()

        assert token.get_balance("user1") == 0

    def test_transfer_tokens(self):
        """Test transferring tokens between users."""
        token = LABDToken()
        token.mint_tokens("user1", 100)
        token.mine_block()

        assert token.transfer("user1", "user2", 30) is True
        token.mine_block()

        assert token.get_balance("user1") == 70
        assert token.get_balance("user2") == 30

    def test_leaderboard(self):
        """Test leaderboard generation."""
        token = LABDToken()
        token.mint_tokens("user1", 100)
        token.mint_tokens("user2", 200)
        token.mint_tokens("user3", 50)
        token.mine_block()

        leaderboard = token.get_leaderboard(limit=3)

        assert len(leaderboard) == 3
        assert leaderboard[0]["address"] == "user2"
        assert leaderboard[0]["balance"] == 200
        assert leaderboard[0]["rank"] == 1

    def test_user_stats(self):
        """Test user statistics."""
        token = LABDToken(reward_amount=10, penalty_amount=5)
        token.mint_tokens("user1", 100)
        token.mine_block()

        token.reward_labeler("user1", "label1")
        token.penalize_labeler("user1", "label2")
        token.mine_block()

        stats = token.get_stats("user1")

        assert stats["total_rewards"] == 10
        assert stats["total_penalties"] == 5
        assert stats["net_earnings"] == 5
        assert stats["balance"] == 105

    def test_global_stats(self):
        """Test global statistics."""
        token = LABDToken()
        token.mint_tokens("user1", 100)
        token.mint_tokens("user2", 50)
        token.mine_block()

        stats = token.get_stats()

        assert stats["total_supply"] >= 150
        assert stats["total_blocks"] >= 1
        assert "total_transactions" in stats


class TestBlockSerialization:
    """Test block and blockchain serialization."""

    def test_block_to_dict(self):
        """Test block serialization."""
        tx = Transaction(sender="user1", recipient="user2", amount=100)
        block = Block(
            index=1,
            timestamp=1234567890.0,
            transactions=[tx],
            previous_hash="abc123"
        )
        block.hash = block.calculate_hash()

        block_dict = block.to_dict()

        assert block_dict["index"] == 1
        assert block_dict["previous_hash"] == "abc123"
        assert len(block_dict["transactions"]) == 1

    def test_blockchain_serialization(self):
        """Test blockchain serialization and deserialization."""
        blockchain1 = Blockchain(difficulty=2)

        tx = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain1.add_transaction(tx)
        blockchain1.mine_pending_transactions("miner1")

        # Serialize
        data = blockchain1.to_dict()

        # Deserialize
        blockchain2 = Blockchain.from_dict(data)

        assert len(blockchain2.chain) == len(blockchain1.chain)
        assert blockchain2.difficulty == blockchain1.difficulty
        assert blockchain2.is_chain_valid()


class TestProofOfWork:
    """Test proof-of-work mining."""

    def test_different_difficulties(self):
        """Test mining with different difficulties."""
        for difficulty in [1, 2, 3]:
            blockchain = Blockchain(difficulty=difficulty)
            tx = Transaction(sender="SYSTEM", recipient="user1", amount=100)
            blockchain.add_transaction(tx)

            block = blockchain.mine_pending_transactions("miner1")

            assert block.hash.startswith("0" * difficulty)
            assert block.nonce > 0

    def test_mining_takes_work(self):
        """Test that mining actually does work (nonce > 1)."""
        blockchain = Blockchain(difficulty=3)
        tx = Transaction(sender="SYSTEM", recipient="user1", amount=100)
        blockchain.add_transaction(tx)

        block = blockchain.mine_pending_transactions("miner1")

        # With difficulty 3, should require significant work
        assert block.nonce > 1
