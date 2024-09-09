

class ReverseIndex:
    def __init__(self) -> None:
        self.index: dict[str, list[int]] = {}

    def add_entry(self, token: str, item_idx: int):
        existing_idxs = self.index.get(token)
        if existing_idxs is None:
            self.index[token] = [item_idx]
        else:
            existing_idxs.append(item_idx)

    def lookup(self, token: str) -> list[int]:
        return self.index.get(token, [])

    def remove_entry(self, token: str, item_idx: int):
        existing_idxs = self.index.get(token)
        if not existing_idxs:
            return
        try:
            idx_of_item = existing_idxs.index(item_idx)
            self.index[token] = existing_idxs[:idx_of_item] + existing_idxs[idx_of_item+1:]
        except ValueError:
            pass

    def update_entry(self, old_text: str, new_text: str, item_idx: int):
        self.remove_entry(old_text, item_idx)
        self.add_entry(new_text, item_idx)
