#!/usr/bin/env python3
"""
Integration test for the Labeled platform.

Tests the complete flow from user registration to consensus and token rewards.
"""

from labeled.consensus import BFTConsensus
from labeled_platform.blockchain import LABDToken

print("=" * 60)
print("LABELED PLATFORM INTEGRATION TEST")
print("=" * 60)
print()

# Test 1: BFT Consensus Algorithm
print("Test 1: BFT Consensus Algorithm")
print("-" * 60)
consensus = BFTConsensus()

# Simulate 10 labelers labeling an image
labels = ["cat"] * 8 + ["dog"] * 2

result = consensus.compute_consensus(labels)

print(f"Labels: {labels}")
print(f"Consensus: {result.consensus_label}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Has Consensus: {result.has_consensus}")
print(f"Byzantine Resistant: {result.is_byzantine_resistant}")

assert result.consensus_label == "cat"
assert result.has_consensus is True
assert result.is_byzantine_resistant is True

print("✓ BFT Consensus test PASSED\n")

# Test 2: LABD Token System
print("Test 2: LABD Token System")
print("-" * 60)

token_system = LABDToken(
    initial_balance=100.0,
    reward_amount=10.0,
    penalty_amount=5.0
)

# Create 3 users
users = ["alice", "bob", "charlie"]

for user in users:
    token_system.mint_tokens(user, 100)

token_system.mine_block()

print(f"Initial balances:")
for user in users:
    balance = token_system.get_balance(user)
    print(f"  {user}: {balance} LABD")

# Reward accurate labelers
token_system.reward_labeler("alice", "label1")
token_system.reward_labeler("bob", "label2")

# Penalize inaccurate labeler
token_system.penalize_labeler("charlie", "label3")

token_system.mine_block()

print(f"\nAfter rewards/penalties:")
for user in users:
    balance = token_system.get_balance(user)
    print(f"  {user}: {balance} LABD")

assert token_system.get_balance("alice") == 110
assert token_system.get_balance("bob") == 110
assert token_system.get_balance("charlie") == 95

print("✓ LABD Token test PASSED\n")

# Test 3: Blockchain Integrity
print("Test 3: Blockchain Integrity")
print("-" * 60)

blockchain = token_system.blockchain

print(f"Total blocks: {len(blockchain.chain)}")
print(f"Difficulty: {blockchain.difficulty}")
print(f"Chain valid: {blockchain.is_chain_valid()}")

assert blockchain.is_chain_valid() is True
assert len(blockchain.chain) >= 2

# Check recent block
latest_block = blockchain.get_latest_block()
print(f"Latest block index: {latest_block.index}")
print(f"Latest block hash: {latest_block.hash[:16]}...")
print(f"Transactions in block: {len(latest_block.transactions)}")

print("✓ Blockchain integrity test PASSED\n")

# Test 4: Complete Labeling Flow
print("Test 4: Complete Labeling Flow")
print("-" * 60)

# Simulate a complete labeling session
print("Simulating data item labeling with consensus...")

# 5 users label the same item
labelers = {
    "user1": "positive",
    "user2": "positive",
    "user3": "positive",
    "user4": "positive",
    "user5": "negative"
}

# Mint tokens for all users
for user in labelers:
    token_system.mint_tokens(user, 100)
token_system.mine_block()

# Collect labels
label_values = list(labelers.values())
consensus_result = consensus.compute_consensus(label_values)

print(f"\nLabels submitted: {label_values}")
print(f"Consensus reached: {consensus_result.consensus_label}")
print(f"Confidence: {consensus_result.confidence:.2%}")

# Distribute rewards/penalties
for user, label_value in labelers.items():
    is_correct = label_value == consensus_result.consensus_label
    if is_correct:
        token_system.reward_labeler(user, f"item1_{user}")
        print(f"  {user}: Correct! +10 LABD (label: {label_value})")
    else:
        token_system.penalize_labeler(user, f"item1_{user}")
        print(f"  {user}: Incorrect. -5 LABD (label: {label_value})")

token_system.mine_block()

print("\nFinal balances:")
for user in labelers:
    balance = token_system.get_balance(user)
    expected = 110 if labelers[user] == consensus_result.consensus_label else 95
    print(f"  {user}: {balance} LABD (expected: {expected})")
    assert balance == expected

print("✓ Complete labeling flow test PASSED\n")

# Test 5: Leaderboard
print("Test 5: Leaderboard")
print("-" * 60)

leaderboard = token_system.get_leaderboard(limit=5)
print("Top 5 token holders:")
for entry in leaderboard[:5]:
    print(f"  {entry['rank']}. {entry['address']}: {entry['balance']} LABD")

assert len(leaderboard) > 0
print("✓ Leaderboard test PASSED\n")

# Test 6: User Statistics
print("Test 6: User Statistics")
print("-" * 60)

stats = token_system.get_stats("user1")
print(f"User statistics for user1:")
print(f"  Balance: {stats['balance']} LABD")
print(f"  Total rewards: {stats['total_rewards']} LABD")
print(f"  Total penalties: {stats['total_penalties']} LABD")
print(f"  Net earnings: {stats['net_earnings']} LABD")

print("✓ User statistics test PASSED\n")

# Summary
print("=" * 60)
print("ALL INTEGRATION TESTS PASSED!")
print("=" * 60)
print()
print("Platform Status:")
print(f"  ✓ BFT Consensus Algorithm working")
print(f"  ✓ LABD Token system operational")
print(f"  ✓ Blockchain integrity maintained")
print(f"  ✓ Complete labeling flow functional")
print(f"  ✓ Leaderboard system working")
print(f"  ✓ User statistics tracking")
print()
print("The Labeled platform is fully operational!")
print("=" * 60)
