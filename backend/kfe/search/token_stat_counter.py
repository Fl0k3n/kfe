import math


class TokenStatCounter:
    def __init__(self) -> None:
        self.token_item_counter: dict[str, int] = {} # token -> number of items where token appeared
        self.item_token_counts: dict[int, dict[str, int]] = {} # item_idx -> {token -> number of times token was in item}
        self.item_lengths: dict[int, int] = {} # number of total tokens in item
        self.total_item_length = 0

    def register(self, tokens: list[str], item_idx: int):
        for token in set(tokens):
            self.token_item_counter[token] = self.token_item_counter.get(token, 0) + 1
        counts = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        self.item_token_counts[item_idx] = counts
        self.total_item_length += len(tokens)
        self.item_lengths[item_idx] = len(tokens)

    def unregister(self, tokens: list[str], item_idx: int):
        '''Reverses register operation, which MUST have been called with the same tokens before calling this.'''
        if item_idx not in self.item_token_counts:
            return
        for token in set(tokens):
            self.token_item_counter[token] -= 1
        self.item_token_counts.pop(item_idx)
        self.total_item_length -= len(tokens)
        self.item_lengths.pop(item_idx)
        
    def idf(self, token: str) -> float:
        N = self.get_number_of_items()
        freq = self.token_item_counter[token]
        return math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    def get_number_of_token_occurances_in_item(self, item_idx: int) -> dict[str, int]:
        return self.item_token_counts[item_idx]

    def get_number_of_items(self) -> int:
        return len(self.item_token_counts)

    def get_avg_item_length(self) -> float:
        if self.get_number_of_items() == 0:
            return 0
        return self.total_item_length / self.get_number_of_items()
    
    def get_item_length(self, item_idx: int) -> int:
        return self.item_lengths[item_idx]
