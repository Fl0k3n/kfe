from typing import Optional

import numpy as np

from search.models import SearchResult


class EmbeddingSimilarityCalculator:

    class Builder:
        def __init__(self) -> None:
            self.row_to_file_id: list[int] = []
            self.file_id_to_row: dict[int, int] = {}
            self.rows: list[np.ndarray] = []

        def add_row(self, file_id, embedding: np.ndarray):
            self.row_to_file_id.append(file_id)
            self.file_id_to_row[file_id] = len(self.rows)
            self.rows.append(embedding)

        def build(self) -> "EmbeddingSimilarityCalculator":
            return EmbeddingSimilarityCalculator(
                row_to_file_id=self.row_to_file_id,
                file_id_to_row=self.file_id_to_row,
                embedding_matrix=np.vstack(self.rows) if len(self.rows) > 0 else None
            )

    def __init__(self, row_to_file_id: list[int], file_id_to_row: dict[int, int], embedding_matrix: Optional[np.ndarray]) -> None:
        self.row_to_file_id = row_to_file_id
        self.file_id_to_row = file_id_to_row
        self.embedding_matrix = embedding_matrix

    def compute_similarity(self, embedding: np.ndarray, k: Optional[int]=None) -> list[SearchResult]:
        if self.embedding_matrix is None:
            return []
        similarities = embedding @ self.embedding_matrix.T
        sorted_by_similarity_asc = np.argsort(similarities)
        if k is None:
            k = len(sorted_by_similarity_asc)
        res = []
        for i in range(len(sorted_by_similarity_asc) - 1, max(len(sorted_by_similarity_asc) - k - 1, -1), -1):
            res.append(SearchResult(
                item_id=self.row_to_file_id[sorted_by_similarity_asc[i]],
                score=similarities[sorted_by_similarity_asc[i]]
            ))
        return res
    
    def get_embedding(self, file_id) -> Optional[np.ndarray]:
        row_id = self.file_id_to_row.get(file_id)
        if row_id is None:
            return None
        return self.embedding_matrix[row_id,:]
