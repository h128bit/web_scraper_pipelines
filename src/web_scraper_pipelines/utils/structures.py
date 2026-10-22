from typing import TypeVar, Generic


T = TypeVar("T")

class LinkedNode(Generic[T]):
    def __init__(self, item: T, depth: int, max_depth: int):
        self._item = item 
        self._max_depth = max_depth 
        self._depth = depth


    def get_children(self, items: list[T]) -> list["LinkedNode[T]"]:
        if self.depth >= self.max_depth:
            return []

        children = []
        for item in items:
            children.append(LinkedNode(item, self.depth+1, self.max_depth))
        return children

    @property
    def item(self) -> T:
        return self._item
        
    @property
    def depth(self) -> int:
        return self._depth

    @property
    def max_depth(self) -> int:
        return self._max_depth
