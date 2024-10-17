from typing import Optional

import numpy as np

from search.models import SearchResult


class MultiEmbeddingSimilarityCalculator:

    class Builder:
        def __init__(self) -> None:
            self.row_to_file_id: list[int] = []
            self.rows: list[np.ndarray] = []

        def add_rows(self, file_id, embeddings: np.ndarray):
            '''Embeddings should be row-wise, all of embeddings should represent this file'''
            for embedding in embeddings:
                self.row_to_file_id.append(int(file_id))
                self.rows.append(embedding)

        def build(self) -> "MultiEmbeddingSimilarityCalculator":
            return MultiEmbeddingSimilarityCalculator(
                row_to_file_id=self.row_to_file_id,
                embedding_matrix=np.vstack(self.rows) if len(self.rows) > 0 else None
            )

    def __init__(self, row_to_file_id: list[int], embedding_matrix: Optional[np.ndarray]) -> None:
        self.row_to_file_id = row_to_file_id
        self.embedding_matrix = embedding_matrix # row-wise

    def compute_similarity(self, embedding: np.ndarray, k: Optional[int]=None) -> list[SearchResult]:
        if self.embedding_matrix is None:
            return []
        similarities = embedding @ self.embedding_matrix.T
        sorted_by_similarity_asc = np.argsort(similarities)
        if k is None:
            k = len(sorted_by_similarity_asc)
        res, item_ids = [], set()
        i = len(sorted_by_similarity_asc) - 1
        while i >= 0 and len(item_ids) < k:
            item_id = self.row_to_file_id[sorted_by_similarity_asc[i]]
            if item_id not in item_ids:
                item_ids.add(item_id)
                res.append(SearchResult(
                    item_id=item_id,
                    score=similarities[sorted_by_similarity_asc[i]]
                ))
            i -= 1
        return res
