from collections import deque
from typing import Generator

import editdistance


class BKTree:
    class Node:
        def __init__(self, word: str):
            self.children: dict[int, "BKTree.Node"] = {}
            self.word = word

    def __init__(self, root_word: str):
        self.root = self.Node(root_word)

    def add(self, word: str):
        cur = self.root
        while True:
            dist = editdistance.eval(word, cur.word)
            if dist == 0:
                return
            child = cur.children.get(dist)
            if child is None:
                cur.children[dist] = self.Node(word)
                break
            else:
                cur = child

    def search(self, word: str, max_distance: int=1) -> Generator[tuple[str, int], None, None]:
        queue: deque["BKTree.Node"] = deque()
        queue.append(self.root)
        while queue:
            cur = queue.popleft()
            dist = editdistance.eval(word, cur.word)
            if dist <= max_distance:
                yield cur.word, dist
            for d in range(max(dist - max_distance, 0), dist + max_distance + 1):
                if next := cur.children.get(d):
                    queue.append(next)
