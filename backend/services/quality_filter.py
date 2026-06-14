from typing import Any, Dict, List

class ResultQualityFilter:
    """Filters low-quality search results and prunes near-duplicates to maximize result cleanliness."""

    @staticmethod
    def filter_results(
        results: List[Dict[str, Any]],
        minimum_score: float = 0.30
    ) -> List[Dict[str, Any]]:
        """
        1. Remove matches scoring below the minimum_score threshold.
        2. Detect and prune near-duplicate text content chunks (keeping the one with the higher score).
        """
        # 1. Filter by threshold
        threshold_filtered = [r for r in results if r.get("score", 0.0) >= minimum_score]

        # 2. Near-duplicate pruning
        pruned_results = []
        seen_contents = set()

        for item in threshold_filtered:
            # Clean content string for robust check
            content_str = item.get("content", "")
            clean_content = "".join(char.lower() for char in content_str if char.isalnum())
            
            if not clean_content:
                continue

            is_duplicate = False
            for seen in seen_contents:
                if clean_content == seen or (len(clean_content) > 15 and (clean_content in seen or seen in clean_content)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                pruned_results.append(item)
                seen_contents.add(clean_content)

        return pruned_results
