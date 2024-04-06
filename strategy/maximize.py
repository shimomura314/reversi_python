"""A strategy to try to maximize the number of disks you have."""

import random


class Maximize:
    def __init__(self):
        pass

    def put_disk(self, othello):
        turn = othello.turn
        max_strategy = []
        max_merit = 0

        candidates = []
        for num in range(64):
            if (pow(2, num)) & othello.reversible:
                candidates.append(num)
        for candidate in candidates:
            new_board = othello.board.simulate_play(
                othello.turn, candidate)
            counter = othello.board.count_disks(*new_board)
            if max_merit < counter[turn]:
                max_strategy = [candidate]
                max_merit = counter[turn]
            elif max_merit == counter[turn]:
                max_strategy.append(candidate)
        return random.choice(max_strategy)
