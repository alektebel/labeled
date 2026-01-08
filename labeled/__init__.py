"""
Labeled: A platform for decentralized labeling of data with Byzantine Fault Tolerant consensus.
"""

from .consensus import BFTConsensus, ConsensusResult

__version__ = "0.1.0"
__all__ = ["BFTConsensus", "ConsensusResult"]
