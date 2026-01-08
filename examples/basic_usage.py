"""
Basic usage examples for the BFT Consensus algorithm.
"""

from labeled import BFTConsensus


def example_simple_consensus():
    """Example: Simple consensus with clear majority."""
    print("=" * 60)
    print("Example 1: Simple Consensus")
    print("=" * 60)

    consensus = BFTConsensus()

    # Simulate 10 labelers classifying an image
    labels = ["cat"] * 8 + ["dog"] * 2

    result = consensus.compute_consensus(labels)

    print(f"Labels: {labels}")
    print(f"Consensus Label: {result.consensus_label}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Agreement: {result.agreement_count}/{result.total_labelers}")
    print(f"Has Consensus: {result.has_consensus}")
    print(f"Byzantine Resistant: {result.is_byzantine_resistant}")
    print(f"Label Distribution: {result.label_distribution}")
    print()


def example_no_consensus():
    """Example: No consensus due to disagreement."""
    print("=" * 60)
    print("Example 2: No Consensus (Disagreement)")
    print("=" * 60)

    consensus = BFTConsensus()

    # Too much disagreement
    labels = ["cat"] * 3 + ["dog"] * 3 + ["bird"] * 2

    result = consensus.compute_consensus(labels)

    print(f"Labels: {labels}")
    print(f"Consensus Label: {result.consensus_label}")
    print(f"Has Consensus: {result.has_consensus}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Label Distribution: {result.label_distribution}")
    print()


def example_byzantine_fault_tolerance():
    """Example: System tolerates Byzantine (malicious) labelers."""
    print("=" * 60)
    print("Example 3: Byzantine Fault Tolerance")
    print("=" * 60)

    consensus = BFTConsensus()

    # 12 labelers: 9 honest, 3 Byzantine (malicious)
    # System can tolerate up to 3 Byzantine nodes (< 1/3)
    # 9/12 = 75% > 66.7%, so consensus is achieved
    honest_labels = ["positive"] * 9
    byzantine_labels = ["spam"] * 3  # Coordinated malicious attack

    labels = honest_labels + byzantine_labels

    result = consensus.compute_consensus(labels)

    max_tolerable = consensus.get_max_tolerable_faults(len(labels))

    print(f"Total Labelers: {len(labels)}")
    print(f"Honest: 9, Byzantine: 3 (coordinated attack)")
    print(f"Max Tolerable Byzantine Faults: {max_tolerable}")
    print(f"Consensus Label: {result.consensus_label}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Byzantine Resistant: {result.is_byzantine_resistant}")
    print(f"Valid Consensus: {consensus.is_consensus_valid(result)}")
    print(f"Result: System successfully tolerates 3 Byzantine labelers!")
    print()


def example_multiclass_labeling():
    """Example: Multiclass labeling with many categories."""
    print("=" * 60)
    print("Example 4: Multiclass Labeling")
    print("=" * 60)

    consensus = BFTConsensus()

    # Sentiment analysis with 5 classes
    labels = [
        "very_positive", "very_positive", "very_positive",
        "very_positive", "very_positive", "very_positive",
        "very_positive",
        "positive", "neutral", "negative"
    ]

    result = consensus.compute_consensus(labels)

    print(f"Task: Sentiment Analysis (5 classes)")
    print(f"Classes: very_positive, positive, neutral, negative, very_negative")
    print(f"Consensus: {result.consensus_label}")
    print(f"Distribution: {result.label_distribution}")
    print(f"Agreement: {result.agreement_count}/{result.total_labelers} ({result.confidence:.1%})")
    print()


def example_batch_processing():
    """Example: Process multiple items in batch."""
    print("=" * 60)
    print("Example 5: Batch Processing")
    print("=" * 60)

    consensus = BFTConsensus()

    # Labels for 3 different images
    batch_labels = [
        ["cat", "cat", "cat", "cat", "dog"],           # Image 1
        ["dog", "dog", "dog", "dog", "dog"],           # Image 2
        ["bird", "bird", "plane", "plane", "bird"],    # Image 3 (ambiguous)
    ]

    results = consensus.compute_batch_consensus(batch_labels)

    for i, result in enumerate(results, 1):
        print(f"Image {i}:")
        print(f"  Consensus: {result.consensus_label}")
        print(f"  Has Consensus: {result.has_consensus}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Distribution: {result.label_distribution}")
    print()


def example_custom_threshold():
    """Example: Custom threshold for stricter consensus."""
    print("=" * 60)
    print("Example 6: Custom Threshold (Stricter)")
    print("=" * 60)

    # Require 80% agreement instead of 66.7%
    strict_consensus = BFTConsensus(supermajority_threshold=0.8)

    labels = ["malignant"] * 7 + ["benign"] * 3  # 70% agreement

    result = strict_consensus.compute_consensus(labels)

    print(f"Threshold: 80% (stricter than default 66.7%)")
    print(f"Labels: 7 malignant, 3 benign (70% agreement)")
    print(f"Has Consensus: {result.has_consensus}")
    print(f"Consensus Label: {result.consensus_label}")
    print()

    # Try with more agreement
    labels2 = ["malignant"] * 9 + ["benign"]  # 90% agreement
    result2 = strict_consensus.compute_consensus(labels2)

    print(f"Labels: 9 malignant, 1 benign (90% agreement)")
    print(f"Has Consensus: {result2.has_consensus}")
    print(f"Consensus Label: {result2.consensus_label}")
    print()


def example_hierarchical_labels():
    """Example: Hierarchical category labels using tuples."""
    print("=" * 60)
    print("Example 7: Hierarchical Labels")
    print("=" * 60)

    consensus = BFTConsensus()

    # Hierarchical classification: (domain, category, subcategory)
    labels = [
        ("animal", "mammal", "cat"),
        ("animal", "mammal", "cat"),
        ("animal", "mammal", "cat"),
        ("animal", "mammal", "cat"),
        ("animal", "mammal", "cat"),
        ("animal", "mammal", "dog"),
        ("animal", "bird", "sparrow")
    ]

    result = consensus.compute_consensus(labels)

    print(f"Hierarchical Classification Result:")
    print(f"Consensus: {result.consensus_label}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Distribution:")
    for label, count in result.label_distribution.items():
        print(f"  {label}: {count}")
    print()


if __name__ == "__main__":
    example_simple_consensus()
    example_no_consensus()
    example_byzantine_fault_tolerance()
    example_multiclass_labeling()
    example_batch_processing()
    example_custom_threshold()
    example_hierarchical_labels()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
