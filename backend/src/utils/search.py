import numpy as np

from search.models import SearchResult


def combine_results_with_rescoring(all_results: list[list[SearchResult]], weights: list[float]) -> list[SearchResult]:
    # meant for results from the same retriever (with scores from the same domain)
    assert len(all_results) == len(weights) and np.isclose(np.sum(weights), 1)
    score_by_id: dict[int, float] = {}
    for dim_results, weight in zip(all_results, weights):
        for sr in dim_results:
            score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + sr.score * weight
    res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
    res.sort(key=lambda x: x.score, reverse=True)
    return res

def reciprocal_rank_fusion(all_results: list[list[SearchResult]], weights: list[float]=None, rrf_k_constant: float=60.) -> list[SearchResult]:
    # each list in all_results must be sorted according to the score assigned by a retriever, with most relevant item first
    # https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
    if len(all_results) == 1:
        return all_results[0]
    if weights is None:
        weights = [1.] * len(all_results)
    assert len(all_results) == len(weights)
    score_by_id: dict[int, float] = {}
    for retriever_results, weight in zip(all_results, weights):
        for rank, sr in enumerate(retriever_results, start=1):
            partial_rrf_score = weight / (rrf_k_constant + rank)
            score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + partial_rrf_score
    res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
    res.sort(key=lambda x: x.score, reverse=True)
    return res
