class Trie:
    class Node:
        def __init__(self, num_tokens: int, is_terminal: bool):
            self.children = [None] * num_tokens
            self.is_terminal = is_terminal

    def __init__(self, num_tokens: int):
        self.num_tokens = num_tokens
        self.root = self.Node(num_tokens=num_tokens, is_terminal=False)

    def add(self, word_token_ids: list[int]):
        if not word_token_ids:
            return
        cur = self.root
        for token in word_token_ids:
            if cur.children[token] is None:
                tmp = self.Node(self.num_tokens, is_terminal=False)
                cur.children[token] = tmp
            cur = cur.children[token]
        cur.is_terminal = True

    def search(self, word_token_ids: list[int]) -> tuple[bool, int, Node]:
        '''Returns: True iff word exists, length of the longest prefix, last Node on the path'''
        cur = self.root
        for i, token in enumerate(word_token_ids):
            if cur.children[token] is None:
                return False, i, cur
            cur = cur.children[token]
        return cur.is_terminal, len(word_token_ids), cur
    
    def has(self, word_token_ids: list[int]) -> bool:
        return self.search(word_token_ids)[0]
    
    def get_possible_next_tokens(self, node: "Trie.Node") -> list[int]:
        if node is None:
            return []
        return [i for i, x in enumerate(node.children) if x is not None] 
