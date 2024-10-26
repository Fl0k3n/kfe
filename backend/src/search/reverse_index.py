

class ReverseIndex:
    def __init__(self) -> None:
        self.index: dict[str, set[int]] = {}

    def add_entry(self, token: str, item_idx: int):
        existing_idxs = self.index.get(token)
        if existing_idxs is None:
            self.index[token] = set([item_idx])
        else:
            existing_idxs.add(item_idx)

    def lookup(self, token: str) -> set[int]:
        return self.index.get(token, set())

    def remove_entry(self, token: str, item_idx: int):
        existing_idxs = self.index.get(token)
        if not existing_idxs or item_idx not in existing_idxs:
            return
        existing_idxs.remove(item_idx)

    def __len__(self) -> int:
        return len(self.index)
