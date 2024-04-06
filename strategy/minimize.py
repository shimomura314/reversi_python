"""A strategy to try to minimize the number of disks you have."""

import random


class Minimize:
    def __init__(self):
        pass

    def put_disk(self, othello):
        turn = othello.turn
        min_strategy = []
        min_merit = float("inf")

        candidates = []
        for num in range(64):
            if (pow(2, num)) & othello.reversible:
                candidates.append(num)
        for candidate in candidates:
            new_board = othello.board.simulate_play(
                othello.turn, candidate)
            counter = othello.board.count_disks(*new_board)
            if min_merit > counter[turn]:
                min_strategy = [candidate]
                min_merit = counter[turn]
            elif min_merit == counter[turn]:
                min_strategy.append(candidate)
        return random.choice(min_strategy)
