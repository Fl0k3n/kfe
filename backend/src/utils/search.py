import numpy as np

from search.models import SearchResult


def combine_results_with_rescoring(all_results: list[list[SearchResult]], weights: list[float]) -> list[SearchResult]:
    assert len(all_results) == len(weights) and np.isclose(np.sum(weights), 1)
    score_by_id: dict[int, float] = {}
    for dim_results, weight in zip(all_results, weights):
        for sr in dim_results:
            score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + sr.score * weight
    res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
    res.sort(key=lambda x: x.score, reverse=True)
    return res
