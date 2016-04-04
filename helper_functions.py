"""File containing helper functions used across all modules."""
import heapq


class DeprecatedError(Exception):
    """Raise if function not used anymore."""

    def __init__(self, value):
        """Overwrite default init."""
        self.value = value

    def __str__(self):
        """Overwrite default string repr."""
        return repr(self.value)


def get_top_elements(item_list, k):
    """Top k elements of a list of tuples.

    First item of the tuple is the key.
    The returned list is a min-heap
    """
    heap = []
    for item in item_list:
        if len(heap) < k:
            heapq.heappush(heap, item)
        elif len(heap) == k:
            if item < heap[0]:
                pass
            else:
                heapq.heappop(heap)
                heapq.heappush(heap, item)
    return heap
