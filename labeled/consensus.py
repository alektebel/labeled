"""
Byzantine Fault Tolerant Consensus Algorithm for Decentralized Data Labeling.

This module implements a BFT consensus mechanism that can tolerate up to f Byzantine
(malicious or faulty) labelers out of n total labelers, where n >= 3f + 1.
"""

from typing import List, Dict, Optional, Any
from collections import Counter
from dataclasses import dataclass


@dataclass
class ConsensusResult:
    """Result of consensus computation.

    Attributes:
        consensus_label: The agreed-upon label, or None if no consensus
        confidence: Confidence score (0.0 to 1.0) based on agreement ratio
        total_labelers: Total number of labelers
        agreement_count: Number of labelers who agreed on the consensus label
        label_distribution: Distribution of all labels
        has_consensus: Whether BFT consensus was reached
        is_byzantine_resistant: Whether enough labelers participated for BFT guarantees
    """
    consensus_label: Optional[Any]
    confidence: float
    total_labelers: int
    agreement_count: int
    label_distribution: Dict[Any, int]
    has_consensus: bool
    is_byzantine_resistant: bool


class BFTConsensus:
    """
    Byzantine Fault Tolerant Consensus for multiclass labeling.

    This implementation uses a supermajority voting approach where:
    - A consensus requires > 2/3 of labelers to agree (tolerates up to 1/3 Byzantine nodes)
    - Minimum of 4 labelers required for BFT guarantees (n >= 3f + 1, where f >= 1)
    - Supports any hashable label type (strings, integers, tuples, etc.)

    For fewer than 4 labelers, simple majority is used with a warning flag.
    """

    def __init__(self, min_labelers: int = 4, supermajority_threshold: float = 2/3):
        """
        Initialize BFT Consensus.

        Args:
            min_labelers: Minimum labelers for BFT guarantees (default: 4, allows f=1)
            supermajority_threshold: Fraction of votes needed for consensus (default: 2/3)

        Raises:
            ValueError: If parameters are invalid
        """
        if min_labelers < 1:
            raise ValueError("min_labelers must be at least 1")
        if not 0.5 < supermajority_threshold <= 1.0:
            raise ValueError("supermajority_threshold must be in range (0.5, 1.0]")

        self.min_labelers = min_labelers
        self.supermajority_threshold = supermajority_threshold

    def compute_consensus(self, labels: List[Any]) -> ConsensusResult:
        """
        Compute BFT consensus from a list of labels.

        Args:
            labels: List of labels from different labelers

        Returns:
            ConsensusResult object with consensus information

        Raises:
            ValueError: If labels list is empty
        """
        if not labels:
            raise ValueError("Labels list cannot be empty")

        # Count label occurrences
        label_counts = Counter(labels)
        total_labelers = len(labels)

        # Find the most common label and its count
        most_common_label, agreement_count = label_counts.most_common(1)[0]

        # Calculate agreement ratio
        agreement_ratio = agreement_count / total_labelers

        # Check if we have BFT resistance (enough labelers)
        is_byzantine_resistant = total_labelers >= self.min_labelers

        # Determine if consensus is reached
        # For BFT: requires > 2/3 supermajority
        # For non-BFT: still apply threshold but flag as not Byzantine-resistant
        has_consensus = agreement_ratio > self.supermajority_threshold

        # Calculate confidence score
        # Confidence is based on how much the agreement exceeds the threshold
        if has_consensus:
            # Scale confidence from threshold to 1.0
            confidence = min(1.0, agreement_ratio)
        else:
            # Scale confidence from 0 to threshold
            confidence = agreement_ratio / self.supermajority_threshold * 0.5

        return ConsensusResult(
            consensus_label=most_common_label if has_consensus else None,
            confidence=confidence,
            total_labelers=total_labelers,
            agreement_count=agreement_count,
            label_distribution=dict(label_counts),
            has_consensus=has_consensus,
            is_byzantine_resistant=is_byzantine_resistant
        )

    def compute_batch_consensus(self, batch_labels: List[List[Any]]) -> List[ConsensusResult]:
        """
        Compute consensus for multiple data items at once.

        Args:
            batch_labels: List of label lists, one per data item

        Returns:
            List of ConsensusResult objects
        """
        return [self.compute_consensus(labels) for labels in batch_labels]

    def get_max_tolerable_faults(self, num_labelers: int) -> int:
        """
        Calculate maximum number of Byzantine faults tolerable.

        Args:
            num_labelers: Number of labelers

        Returns:
            Maximum number of Byzantine (faulty/malicious) labelers tolerable
        """
        # For BFT with supermajority, we can tolerate f < n/3
        # With 2/3 threshold: f = floor((n-1)/3)
        if num_labelers < self.min_labelers:
            return 0
        return (num_labelers - 1) // 3

    def is_consensus_valid(self, result: ConsensusResult) -> bool:
        """
        Check if a consensus result is valid and Byzantine-resistant.

        Args:
            result: ConsensusResult to validate

        Returns:
            True if consensus is reached and Byzantine-resistant
        """
        return result.has_consensus and result.is_byzantine_resistant
