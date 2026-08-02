from collections import deque


class WorkingMemory:
    def __init__(self, max_items: int = 8):
        self.items = deque(maxlen=max_items)

    def add(self, text: str):
        self.items.append(text)

    def render(self):
        return "\n".join(self.items)