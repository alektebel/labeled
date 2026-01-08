"""
Comprehensive tests for Byzantine Fault Tolerant Consensus algorithm.
"""

import pytest
from labeled.consensus import BFTConsensus, ConsensusResult


class TestBFTConsensusInitialization:
    """Test consensus initialization and parameter validation."""

    def test_default_initialization(self):
        """Test default parameters."""
        consensus = BFTConsensus()
        assert consensus.min_labelers == 4
        assert consensus.supermajority_threshold == 2/3

    def test_custom_initialization(self):
        """Test custom parameters."""
        consensus = BFTConsensus(min_labelers=7, supermajority_threshold=0.75)
        assert consensus.min_labelers == 7
        assert consensus.supermajority_threshold == 0.75

    def test_invalid_min_labelers(self):
        """Test that invalid min_labelers raises error."""
        with pytest.raises(ValueError, match="min_labelers must be at least 1"):
            BFTConsensus(min_labelers=0)

    def test_invalid_threshold_too_low(self):
        """Test that threshold <= 0.5 raises error."""
        with pytest.raises(ValueError, match="supermajority_threshold must be in range"):
            BFTConsensus(supermajority_threshold=0.5)

    def test_invalid_threshold_too_high(self):
        """Test that threshold > 1.0 raises error."""
        with pytest.raises(ValueError, match="supermajority_threshold must be in range"):
            BFTConsensus(supermajority_threshold=1.1)


class TestBasicConsensus:
    """Test basic consensus scenarios."""

    def test_unanimous_consensus(self):
        """Test unanimous agreement among labelers."""
        consensus = BFTConsensus()
        labels = ["cat", "cat", "cat", "cat", "cat"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "cat"
        assert result.has_consensus is True
        assert result.confidence == 1.0
        assert result.total_labelers == 5
        assert result.agreement_count == 5
        assert result.is_byzantine_resistant is True

    def test_supermajority_consensus(self):
        """Test consensus with exactly 2/3 + 1 agreement."""
        consensus = BFTConsensus()
        # 5 labelers: need 4 for >2/3 (66.7%)
        labels = ["dog", "dog", "dog", "dog", "cat"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "dog"
        assert result.has_consensus is True
        assert result.agreement_count == 4
        assert result.total_labelers == 5
        assert result.confidence == 0.8
        assert result.is_byzantine_resistant is True

    def test_no_consensus_insufficient_majority(self):
        """Test no consensus when insufficient agreement."""
        consensus = BFTConsensus()
        # 6 labelers: need 5 for >2/3, only have 4 (exactly 2/3, not enough)
        labels = ["dog", "dog", "dog", "dog", "cat", "bird"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label is None
        assert result.has_consensus is False
        assert result.agreement_count == 4
        # 4/6 = exactly 2/3, confidence = 0.5 (at threshold boundary)
        assert result.confidence == 0.5

    def test_tie_scenario(self):
        """Test tie scenario (no label reaches threshold)."""
        consensus = BFTConsensus()
        labels = ["cat", "cat", "dog", "dog"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label is None
        assert result.has_consensus is False
        assert result.total_labelers == 4


class TestByzantineFaultTolerance:
    """Test Byzantine fault tolerance capabilities."""

    def test_tolerates_one_third_byzantine_nodes(self):
        """Test system tolerates up to 1/3 Byzantine (malicious) labelers."""
        consensus = BFTConsensus()
        # 7 honest labelers say "correct", 2 Byzantine say "wrong", 1 Byzantine says "fake"
        # Total: 10 labelers, 7/10 = 70% > 66.7%
        labels = ["correct"] * 7 + ["wrong"] * 2 + ["fake"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "correct"
        assert result.has_consensus is True
        assert result.is_byzantine_resistant is True
        # Verify we can tolerate 3 Byzantine nodes
        assert consensus.get_max_tolerable_faults(10) == 3

    def test_fails_with_more_than_one_third_byzantine(self):
        """Test system fails when > 1/3 are Byzantine."""
        consensus = BFTConsensus()
        # 6 honest, 4 Byzantine - exceeds tolerance
        labels = ["correct"] * 6 + ["wrong"] * 4
        result = consensus.compute_consensus(labels)

        # Still picks most common, but only 60% < 66.7% threshold
        assert result.has_consensus is False
        assert result.label_distribution["correct"] == 6
        assert result.label_distribution["wrong"] == 4

    def test_coordinated_byzantine_attack(self):
        """Test coordinated attack where Byzantine nodes vote together."""
        consensus = BFTConsensus()
        # 9 honest say "truth", 3 Byzantine coordinate on "lie"
        # 9/12 = 75% > 66.7%, consensus achieved
        labels = ["truth"] * 9 + ["lie"] * 3
        result = consensus.compute_consensus(labels)

        # Honest nodes form strict supermajority (9/12 = 75% > 66.7%)
        assert result.consensus_label == "truth"
        assert result.has_consensus is True

    def test_max_tolerable_faults_calculation(self):
        """Test calculation of maximum tolerable Byzantine faults."""
        consensus = BFTConsensus(min_labelers=4)

        assert consensus.get_max_tolerable_faults(4) == 1   # (4-1)//3 = 1
        assert consensus.get_max_tolerable_faults(7) == 2   # (7-1)//3 = 2
        assert consensus.get_max_tolerable_faults(10) == 3  # (10-1)//3 = 3
        assert consensus.get_max_tolerable_faults(3) == 0   # Below min_labelers


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_labels_raises_error(self):
        """Test that empty labels list raises error."""
        consensus = BFTConsensus()
        with pytest.raises(ValueError, match="Labels list cannot be empty"):
            consensus.compute_consensus([])

    def test_single_labeler(self):
        """Test with single labeler (no BFT resistance)."""
        consensus = BFTConsensus(min_labelers=4)
        labels = ["cat"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "cat"
        assert result.has_consensus is True
        assert result.is_byzantine_resistant is False  # Not enough labelers
        assert result.total_labelers == 1
        assert result.confidence == 1.0

    def test_two_labelers_agreement(self):
        """Test with two labelers in agreement."""
        consensus = BFTConsensus(min_labelers=4)
        labels = ["dog", "dog"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "dog"
        assert result.has_consensus is True
        assert result.is_byzantine_resistant is False

    def test_three_labelers_threshold(self):
        """Test with three labelers at BFT boundary."""
        consensus = BFTConsensus(min_labelers=4)
        labels = ["cat", "cat", "dog"]
        result = consensus.compute_consensus(labels)

        # 2/3 = 66.67%, need > 66.67%
        assert result.has_consensus is False
        assert result.is_byzantine_resistant is False


class TestMulticlassLabeling:
    """Test multiclass labeling scenarios."""

    def test_integer_labels(self):
        """Test with integer class labels."""
        consensus = BFTConsensus()
        # Need >2/3: with 6 labelers, need 5 for consensus
        labels = [0, 0, 0, 0, 0, 1]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == 0
        assert result.has_consensus is True
        assert result.confidence > 0.8

    def test_many_classes(self):
        """Test with many different classes."""
        consensus = BFTConsensus()
        # 10 labelers, 7 agree on class "A"
        labels = ["A"] * 7 + ["B", "C", "D"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "A"
        assert len(result.label_distribution) == 4
        assert result.label_distribution["A"] == 7

    def test_tuple_labels(self):
        """Test with tuple labels (e.g., hierarchical categories)."""
        consensus = BFTConsensus()
        labels = [
            ("animal", "cat"),
            ("animal", "cat"),
            ("animal", "cat"),
            ("animal", "cat"),
            ("animal", "dog")
        ]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == ("animal", "cat")
        assert result.has_consensus is True

    def test_label_distribution(self):
        """Test label distribution tracking."""
        consensus = BFTConsensus()
        labels = ["cat"] * 5 + ["dog"] * 3 + ["bird"] * 2
        result = consensus.compute_consensus(labels)

        assert result.label_distribution == {"cat": 5, "dog": 3, "bird": 2}
        assert result.total_labelers == 10


class TestBatchProcessing:
    """Test batch consensus computation."""

    def test_batch_consensus(self):
        """Test computing consensus for multiple items."""
        consensus = BFTConsensus()
        batch = [
            ["cat", "cat", "cat", "cat"],
            ["dog", "dog", "dog", "dog", "cat"],
            ["bird", "bird", "cat", "dog"]
        ]
        results = consensus.compute_batch_consensus(batch)

        assert len(results) == 3
        assert results[0].consensus_label == "cat"
        assert results[1].consensus_label == "dog"
        assert results[2].consensus_label is None  # No consensus

    def test_empty_batch(self):
        """Test empty batch."""
        consensus = BFTConsensus()
        results = consensus.compute_batch_consensus([])
        assert results == []


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def test_perfect_confidence(self):
        """Test confidence with unanimous vote."""
        consensus = BFTConsensus()
        labels = ["cat"] * 10
        result = consensus.compute_consensus(labels)
        assert result.confidence == 1.0

    def test_high_confidence(self):
        """Test high confidence with strong supermajority."""
        consensus = BFTConsensus()
        labels = ["cat"] * 9 + ["dog"]
        result = consensus.compute_consensus(labels)
        assert result.confidence == 0.9
        assert result.has_consensus is True

    def test_low_confidence_no_consensus(self):
        """Test low confidence when no consensus."""
        consensus = BFTConsensus()
        labels = ["cat"] * 3 + ["dog"] * 3
        result = consensus.compute_consensus(labels)
        assert result.confidence < 0.5
        assert result.has_consensus is False


class TestConsensusValidation:
    """Test consensus validation utility."""

    def test_valid_consensus(self):
        """Test validation of valid consensus."""
        consensus = BFTConsensus()
        labels = ["cat"] * 8 + ["dog"] * 2
        result = consensus.compute_consensus(labels)

        assert consensus.is_consensus_valid(result) is True

    def test_invalid_consensus_no_agreement(self):
        """Test validation fails without consensus."""
        consensus = BFTConsensus()
        labels = ["cat"] * 2 + ["dog"] * 2
        result = consensus.compute_consensus(labels)

        assert consensus.is_consensus_valid(result) is False

    def test_invalid_consensus_insufficient_labelers(self):
        """Test validation fails with too few labelers."""
        consensus = BFTConsensus(min_labelers=5)
        labels = ["cat"] * 3
        result = consensus.compute_consensus(labels)

        assert consensus.is_consensus_valid(result) is False


class TestCustomThresholds:
    """Test custom threshold configurations."""

    def test_higher_threshold(self):
        """Test with stricter threshold (75%)."""
        consensus = BFTConsensus(supermajority_threshold=0.75)
        labels = ["cat"] * 7 + ["dog"] * 3  # 70%
        result = consensus.compute_consensus(labels)

        assert result.has_consensus is False  # 70% < 75%

        labels2 = ["cat"] * 8 + ["dog"] * 2  # 80%
        result2 = consensus.compute_consensus(labels2)
        assert result2.has_consensus is True  # 80% > 75%

    def test_lower_threshold(self):
        """Test with more lenient threshold (60%)."""
        consensus = BFTConsensus(supermajority_threshold=0.6)
        labels = ["cat"] * 6 + ["dog"] * 4  # 60%
        result = consensus.compute_consensus(labels)

        assert result.has_consensus is False  # Need > 60%, not >= 60%

        labels2 = ["cat"] * 7 + ["dog"] * 3  # 70%
        result2 = consensus.compute_consensus(labels2)
        assert result2.has_consensus is True


class TestRealWorldScenarios:
    """Test realistic labeling scenarios."""

    def test_crowdsourcing_scenario(self):
        """Test typical crowdsourcing with some noise."""
        consensus = BFTConsensus()
        # 15 labelers: 11 correct, 3 careless mistakes, 1 malicious
        labels = ["positive"] * 11 + ["negative"] * 3 + ["spam"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "positive"
        assert result.has_consensus is True
        assert result.confidence > 0.7
        # Can tolerate 4 Byzantine, we have 4 wrong
        assert consensus.get_max_tolerable_faults(15) == 4

    def test_expert_panel_scenario(self):
        """Test small expert panel (fewer labelers)."""
        consensus = BFTConsensus(min_labelers=3, supermajority_threshold=0.7)
        # 5 experts, 4 agree
        labels = ["malignant"] * 4 + ["benign"]
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "malignant"
        assert result.has_consensus is True
        assert result.is_byzantine_resistant is True

    def test_adversarial_scenario(self):
        """Test adversarial environment with coordinated attack."""
        consensus = BFTConsensus()
        # 20 labelers: 14 honest, 6 adversarial (just under 1/3)
        labels = ["legitimate"] * 14 + ["spam"] * 6
        result = consensus.compute_consensus(labels)

        assert result.consensus_label == "legitimate"
        assert result.has_consensus is True
        # Verify BFT holds with 6 adversaries (< 7 max tolerable)
        assert consensus.get_max_tolerable_faults(20) == 6
