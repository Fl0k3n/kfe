from typing import Optional

import numpy as np
from sqlalchemy import Column

from kfe.search.models import SearchResult


class EmbeddingSimilarityCalculator:

    class Builder:
        def __init__(self) -> None:
            self.row_to_file_id: list[int] = []
            self.file_id_to_row: dict[int, int] = {}
            self.rows: list[np.ndarray] = []

        def add_row(self, file_id: int | Column[int], embedding: np.ndarray):
            self.row_to_file_id.append(int(file_id))
            self.file_id_to_row[int(file_id)] = len(self.rows)
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
        self.embedding_matrix = embedding_matrix # row-wise

    def compute_similarity(self, embedding: np.ndarray, k: Optional[int]=None) -> list[SearchResult]:
        # TODO if it becomes slow consider running it in executor and making this async
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
    
    def get_embedding(self, file_id: int | Column[int]) -> Optional[np.ndarray]:
        row_id = self.file_id_to_row.get(int(file_id))
        if row_id is None:
            return None
        return self.embedding_matrix[row_id,:]
    
    def replace(self, file_id: int | Column[int], embedding: np.ndarray):
        self.embedding_matrix[self.file_id_to_row[int(file_id)]] = embedding

    def add(self, file_id: int | Column[int], embedding: np.ndarray):
        file_id = int(file_id)
        self.row_to_file_id.append(file_id)
        if self.embedding_matrix is None:
            self.embedding_matrix = np.array([embedding])
        else:
            self.embedding_matrix = np.append(self.embedding_matrix, [embedding], axis=0)
        self.file_id_to_row[file_id] = self.embedding_matrix.shape[0] - 1

    def delete(self, file_id: int | Column[int]):
        # assumed to be called rarely, might be slow
        if int(file_id) not in self.file_id_to_row:
            return
        if len(self.file_id_to_row) == 1:
            self.file_id_to_row, self.row_to_file_id, self.embedding_matrix = {}, [], None
        else:
            row = self.file_id_to_row.pop(int(file_id))
            for fid, old_row in self.file_id_to_row.items():
                if old_row > row:
                    self.file_id_to_row[fid] = old_row - 1
            self.row_to_file_id.pop(row)
            self.embedding_matrix = np.delete(self.embedding_matrix, row, axis=0)
