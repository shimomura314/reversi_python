"""Various strategies for othello.
"""

from collections import deque
import copy
import numpy as np
import pickle
import random

from bitboard import OthelloGame


class MinmaxNew:
    """Find a better move by min-max method.
    """
    __all__ = ["put_disk"]

    def __init__(self, filename="./strategy/minmax_hash.pkl"):
        self._filename = filename
        try:
            with open(filename, "rb") as file_:
                self._hash_log = pickle.load(file_)
        except FileNotFoundError:
            self._hash_log = {}
        for color in ["1", "0"]:
            for turn in ["1", "0"]:
                for depth in map(str, range(10)):
                    key = "".join([color, turn, depth])
                    if key not in self._hash_log.keys():
                        self._hash_log[key] = {}

        self._EVALUATION_FIRST = [
            30,  -12,   0,  -1,  -1,   0, -12,  30,
            -12, -15,  -3,  -3,  -3,  -3, -15, -12,
            0,    -3,   0,  -1,  -1,   0,  -3,   0,
            -1,   -3,  -1,  -1,  -1,  -1,  -3,  -1,
            -1,   -3,  -1,  -1,  -1,  -1,  -3,  -1,
            0,    -3,   0,  -1,  -1,   0,  -3,   0,
            -12, -15,  -3,  -3,  -3,  -3, -15, -12,
            30,  -12,   0,  -1,  -1,   0, -12,  30,
        ]
        self._EVALUATION_MIDDLE = [
            120, -20,  20,   5,   5,  20, -20, 120,
            -20, -40,  -5,  -5,  -5,  -5, -40, -20,
            20,   -5,  15,   3,   3,  15,  -5,  20,
            5,    -5,   3,   3,   3,   3,  -5,   5,
            5,    -5,   3,   3,   3,   3,  -5,   5,
            20,   -5,  15,   3,   3,  15,  -5,  20,
            -20, -40,  -5,  -5,  -5,  -5, -40, -20,
            120, -20,  20,   5,   5,  20, -20, 120,
        ]

        self._EXP2 = [pow(2, num) for num in range(64)]
        return

    def touch_border(self, black_board, white_board):
        board = (white_board | black_board)
        if board & 0xff818181818181ff:
            return 1
        return 0

    # def openness(
    #         self, black_board: int, white_board: int,
    #         turn: int, candidate:int):
    #     """Calculate openness.

    #     未完成　難しくない？

    #     Parameters
    #     ----------
    #     candidate : int
    #         Integer from 0 to 63.
    #     """
    #     input_ = self._EXP2[candidate]
    #     if turn:
    #         return self.bit_count(black_board), self.bit_count(white_board)
    #     else:
    #         return self.bit_count(white_board), self.bit_count(black_board)
    #     blank_board = ~(black_board | white_board)

    #     reverse_bit = 0
    #     for direction in range(8):
    #         reverse_bit_ = 0
    #         border_bit = self._othello.board.check_surroundings(
    #             input_, direction)
    #         while (border_bit != 0) and ((border_bit & opponent) != 0):
    #             reverse_bit_ |= border_bit
    #             border_bit = self.check_surroundings(border_bit, direction)
    #         if (border_bit & player) != 0:
    #             reverse_bit |= reverse_bit_

    #     reversed_disk = []
    #     for num in range(64):
    #         if self._EXP2[num]&reverse_bit:
    #             reversed_disk.append(num)
    #     print("reversed_disk", reversed_disk)

    #     openness_value = 0
    #     print(candidate, openness_value)
    #     return openness_value

    def static_evaluation_function(
            self, white_board: int, black_board: int, stage: int) -> int:
        """Definition of static function."""
        board_evaluation = 0
        board = [black_board, white_board]

        if stage < 21:
            for position in range(64):
                if (self._EXP2[position] & board[self._player_clr ^ 1]):
                    board_evaluation += self._EVALUATION_FIRST[position]
                if (self._EXP2[position] & board[self._player_clr]):
                    board_evaluation -= self._EVALUATION_FIRST[position]
        else:
            for position in range(64):
                if (self._EXP2[position] & board[self._player_clr ^ 1]):
                    board_evaluation += self._EVALUATION_MIDDLE[position]
                if (self._EXP2[position] & board[self._player_clr]):
                    board_evaluation -= self._EVALUATION_MIDDLE[position]
        return board_evaluation

    def check_hash_table(self, hashed_board, hash_key):
        """Save board data which is deeper than 4."""
        if hashed_board in self._hash_log[hash_key].keys():
            return True, self._hash_log[hash_key][hashed_board]
        return False, None

    def save_hash_table(
            self, hashed_board, hash_key, evaluation, selected, depth
            ):
        if depth < 4:
            return
        self._hash_log[hash_key][hashed_board] = (evaluation, selected)
        return

    def update_file(self):
        with open(self._filename, "wb") as file_:
            pickle.dump(self._hash_log, file_)
        return

    def move_ordering(
            self, white_board: int, black_board: int, turn: int,
            reversible: int, candidates: list, stage: int,
            ) -> list:
        """Define order of moves, so that you can find next move effectively.
        For move ordering, values below are used.
            Opening(0~20) : evaluate_value, available moves
            Middle game(21~47) : evaluate_value
            Endgame(48~64) : number of available moves(Fastest-first find)

        Returns
        -------
        candidates : list of ints
            List of integers orderd by possibility.
        """
        # print("order")

        ordered_candidates = []
        if not reversible:
            return ordered_candidates
        # Killer move(corner)
        if reversible & 0x1:
            ordered_candidates.append([1000000, 0])
        if reversible & 0x80:
            ordered_candidates.append([1000000, 7])
        if reversible & 0x100000000000000:
            ordered_candidates.append([1000000, 56])
        if reversible & 0x8000000000000000:
            ordered_candidates.append([1000000, 63])
        # print("init candidates", candidates)
        for number, candidate in enumerate(candidates):
            new_white_board, new_black_board = \
                self._othello.board.put_disk(
                    turn, self._EXP2[candidate], False,
                    black_board, white_board,
                )

            if stage < 21:
                usable_moves = self._othello.board.reversible_area(
                    turn ^ 1, new_white_board, new_black_board
                    )
                usable_moves = self._othello.board.bit_count(usable_moves)
                board_evaluation = self.static_evaluation_function(
                    new_white_board, new_black_board, stage=stage)
                evaluation = -5*usable_moves + board_evaluation
                # print(stage, usable_moves, board_evaluation)
            elif 21 <= stage < 48:
                board_evaluation = self.static_evaluation_function(
                    new_white_board, new_black_board, stage=stage)
                evaluation = board_evaluation
                # print(stage, board_evaluation)
            else:
                usable_moves = self._othello.board.reversible_area(
                    turn ^ 1, new_white_board, new_black_board
                    )
                usable_moves = self._othello.board.bit_count(usable_moves)
                evaluation = -1*usable_moves
                # print(stage, usable_moves)

            ordered_candidates.append([evaluation, candidate])
        ordered_candidates.sort(reverse=True)
        # ordered_candidates = np.uint64(np.array(ordered_candidates))
        ordered_candidates = np.array(ordered_candidates)
        # print(ordered_candidates)
        return ordered_candidates[:, 1]

    def search_candidates(self, reversible: int) -> list:
        """Count the number of bit awaking.

        Parameters
        ----------
        reversible : int
            64-bit intager.

        Returns
        -------
        candidates : list of ints
            List of integers from 0 to 63.
        """
        candidates = []
        for position in range(64):
            if reversible & self._EXP2[position]:
                candidates.append(position)
        return candidates

    def min_max(
            self, white_board: int, black_board: int, turn: int,
            depth: int, pre_evaluation=-1*float("inf"),
            ):
        # If the board is known, return value.
        # print("called, game turn = %d, depth = %d, pre = %f" %(turn, depth, pre_evaluation))
        hashed_board = "".join([str(white_board), str(black_board)])
        hash_key = "".join([str(self._player_clr) + str(turn) + str(depth)])

        is_exist, saved = self.check_hash_table(hashed_board, hash_key)
        if is_exist:
            evaluation, selected = saved
            # print("exist, evaluation = %d, selected = %d, depth = %d" %(evaluation, selected, depth))
            return evaluation, selected

        # Calculate evaluation.
        stage = sum(self._othello.board.count_disks(black_board, white_board))
        if depth == 0:
            if stage < 21:
                # print("return root evaluation = %d" %(evaluation))
                usable_moves = self._othello.board.reversible_area(
                    turn, black_board, white_board
                    )
                usable_moves = self._othello.board.bit_count(usable_moves)
                board_evaluation = self.static_evaluation_function(
                    black_board, white_board, stage)
                evaluation = -5*usable_moves + board_evaluation
                return evaluation, 1
            else:
                evaluation = self.static_evaluation_function(
                    black_board, white_board, stage)
                return evaluation, 1

        if turn == self._player_clr:
            max_evaluation = -1*float("inf")
        else:
            min_evaluation = float("inf")

        reversible = self._othello.board.reversible_area(
            turn, black_board, white_board)
        if depth > 4:
            pre_candidates = self.search_candidates(reversible)
            candidates = self.move_ordering(
                black_board, white_board, turn,
                reversible, pre_candidates, stage,
                )
        else:
            candidates = self.search_candidates(reversible)

        # print("pre candidates", candidates)
        if self._othello.board.turn_playable(
                turn, black_board, white_board):
            for candidate in candidates:
                new_black_board, new_white_board = \
                    self._othello.board.put_disk(
                        turn, self._EXP2[candidate], False,
                        black_board, white_board,
                    )

                count_white, count_black = self._othello.board.count_disks(
                    new_white_board, new_black_board
                )
                if self._player_clr:
                    count_player, count_opponent = count_black, count_white
                else:
                    count_player, count_opponent = count_white, count_black
                count_blank = 64 - count_player - count_opponent

                if self._othello.judge_game(
                        count_player, count_opponent, count_blank):
                    if self._result == "WIN":
                        next_evaluation = count_player*1000
                    elif self._result == "LOSE":
                        next_evaluation = -count_opponent*1000
                    else:
                        next_evaluation = 0
                else:
                    if turn == self._player_clr:
                        # print("call function, candidate = %d, depth = %d" %(candidate, depth))
                        next_evaluation = self.min_max(
                            new_white_board, new_black_board, turn ^ 1,
                            depth-1, max_evaluation,
                            )[0]
                    else:
                        # print("call function, candidate = %d, depth = %d" %(candidate, depth))
                        next_evaluation = self.min_max(
                            new_white_board, new_black_board, turn ^ 1,
                            depth-1, min_evaluation,
                            )[0]

                # alpha-bata method(pruning)
                if turn == self._player_clr:
                    # print("beta cut, pre=%f < next=%f or not" %(pre_evaluation, next_evaluation))
                    if next_evaluation > pre_evaluation:
                        # print("cut, candidate = %d, depth = %d" %(candidate, depth))
                        return pre_evaluation, candidate
                else:
                    # print("alpha cut, pre=%f > next=%f or not" %(pre_evaluation, next_evaluation))
                    if pre_evaluation > next_evaluation:
                        # print("cut, candidate = %d, depth = %d" %(candidate, depth))
                        return pre_evaluation, candidate

                if turn == self._player_clr:
                    if max_evaluation < next_evaluation:
                        max_evaluation = next_evaluation
                        selected = candidate
                        # print("new max", max_evaluation)
                else:
                    if next_evaluation < min_evaluation:
                        min_evaluation = next_evaluation
                        selected = candidate
                        # print("new min", min_evaluation)
        else:
            # print("pass", turn, depth)
            if turn == self._player_clr:
                return self.min_max(
                    black_board, white_board, turn ^ 1,
                    depth-1, max_evaluation
                    )
            else:
                return self.min_max(
                    black_board, white_board, turn ^ 1,
                    depth-1, min_evaluation,
                    )
        if turn == self._player_clr:
            if depth > 4:
                self.save_hash_table(
                    hashed_board, hash_key, max_evaluation, selected, depth)
            # print("final value = %f, selected = %d, game turn %d, depth = %d" %(max_evaluation, selected, turn, depth))
            return max_evaluation, selected
        else:
            if depth > 4:
                self.save_hash_table(
                    hashed_board, hash_key, min_evaluation, selected, depth)
            # print("final value = %f, selected = %d, game turn %d, depth = %d" %(min_evaluation, selected, turn, depth))
            return min_evaluation, selected

    def put_disk(self, othello, depth=5):
        # print()
        # print()
        # print("initial call")
        black_board, white_board = othello.board.return_board()
        turn = othello.turn
        self._player_clr = turn
        self._count_pass = 0
        self._othello = othello
        # x = self.min_max(black_board, white_board, turn, depth, pre_evaluation=float("inf"))[1]
        # print(x)
        # return int(x)
        return int(
            self.min_max(
                black_board, white_board, turn,
                depth, pre_evaluation=float("inf"),
                )[1])
