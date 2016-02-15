"""File containing helper functions used across all modules."""
import heapq


def get_top_elements(item_list, k):
    """Top k elements of a list of tuples.

    First item of the tuple is the key.
    """
    heap = []
    for item in item_list:
        if len(heap) < k or item > heap[0]:
            if len(heap) == k:
                heapq.heappop(heap)

            heapq.heappush(heap, item)

    return heap
