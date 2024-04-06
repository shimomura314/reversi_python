"""A strategy to try to maximize the number of disks you have."""

import random


class Random:
    """Put disk randomly."""
    def __init__(self):
        return

    def put_disk(self, othello):
        """Put disk randomly."""
        candidates = []
        for num in range(64):
            if (pow(2, num)) & othello.reversible:
                candidates.append(num)
        return random.choice(candidates)
