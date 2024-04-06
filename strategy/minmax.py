"""Various strategies for othello."""
import pickle


class Minmax:
    """Find a better move by min-max method."""

    __all__ = ["put_disk"]

    def __init__(self, depth = 4):
        self._EVAL_TBL = [
            # 1st evaluation table
            [
                30,  -12,   0,  -1,  -1,   0, -12,  30,
                -12, -15,  -3,  -3,  -3,  -3, -15, -12,
                0,    -3,   0,  -1,  -1,   0,  -3,   0,
                -1,   -3,  -1,  -1,  -1,  -1,  -3,  -1,
                -1,   -3,  -1,  -1,  -1,  -1,  -3,  -1,
                0,    -3,   0,  -1,  -1,   0,  -3,   0,
                -12, -15,  -3,  -3,  -3,  -3, -15, -12,
                30,  -12,   0,  -1,  -1,   0, -12,  30,
            ],
            # 2nd evaluation table
            [
                120, -20,  20,   5,   5,  20, -20, 120,
                -20, -40,  -5,  -5,  -5,  -5, -40, -20,
                20,   -5,  15,   3,   3,  15,  -5,  20,
                5,    -5,   3,   3,   3,   3,  -5,   5,
                5,    -5,   3,   3,   3,   3,  -5,   5,
                20,   -5,  15,   3,   3,  15,  -5,  20,
                -20, -40,  -5,  -5,  -5,  -5, -40, -20,
                120, -20,  20,   5,   5,  20, -20, 120,
            ],
        ]

        self._EXP2 = [pow(2, num) for num in range(64)]
        self._depth = depth

    def touch_border(self, black_board, white_board):
        board = (black_board | white_board)
        if board & 0xff818181818181ff:
            return 1
        return 0

    def evaluate_value(self, black_board, white_board):
        evaluation = 0
        board = [black_board, white_board]

        # If disk does not touch the border,
        # phase is False and TABLE[0] is called.
        phase = self.touch_border(black_board, white_board)
        for position in range(64):
            if (self._EXP2[position] & board[self._player_clr]):
                evaluation += self._EVAL_TBL[phase][position]
            if (self._EXP2[position] & board[self._player_clr ^ 1]):
                evaluation -= self._EVAL_TBL[phase][position]
        return evaluation

    def update_file(self):
        with open(self._filename, "wb") as file_:
            pickle.dump(self._hash_log, file_)

    def min_max(
            self, black_board, white_board, turn, depth, pre_evaluation
            ):
        """Return wheather you can put disk or not.

        Parameters
        ----------
        black_board, white_board : int (optional)
            64-bit intager.
        turn : int
            If black is on turn, 1. If white, 0.
        """
        # Calculate evaluation.
        evaluation = self.evaluate_value(black_board, white_board)
        if depth == 0:
            return evaluation, 1

        if turn == self._player_clr:
            max_evaluation = -1 * float("inf")
        else:
            min_evaluation = float("inf")

        reversible = self._othello.board.reversible_area(
            turn, black_board, white_board
            )

        candidates = []
        for num in range(64):
            if self._EXP2[num] & reversible:
                candidates.append(num)

        if self._othello.board.turn_playable(
            turn, black_board, white_board
        ):
            for candidate in candidates:
                new_black_board, new_white_board = \
                    self._othello.board.simulate_play(
                        turn, self._EXP2[candidate],
                        black_board, white_board,
                    )
                count_black, count_white = self._othello.board.count_disks(
                    new_black_board, new_white_board
                )
                if self._player_clr:
                    count_player, count_opponent = count_black, count_white
                else:
                    count_player, count_opponent = count_white, count_black
                if self._othello.judge_game([count_player, count_opponent]):
                    if self._othello.result == "WIN":
                        next_evaluation = 10000000000
                    elif self._othello.result == "LOSE":
                        next_evaluation = -10000000000
                    else:
                        next_evaluation = 0
                else:
                    if turn == self._player_clr:
                        next_evaluation = self.min_max(
                            new_black_board, new_white_board,
                            turn ^ 1, depth-1, max_evaluation,
                            )[0]
                    else:
                        next_evaluation = self.min_max(
                            new_black_board, new_white_board,
                            turn ^ 1, depth-1, min_evaluation,
                            )[0]

                # alpha-bata method(pruning)
                if turn == self._player_clr:
                    if next_evaluation > pre_evaluation:
                        return pre_evaluation, candidate
                else:
                    if pre_evaluation > next_evaluation:
                        return pre_evaluation, candidate

                if turn == self._player_clr:
                    if max_evaluation < next_evaluation:
                        max_evaluation = next_evaluation
                        selected = candidate
                else:
                    if next_evaluation < min_evaluation:
                        min_evaluation = next_evaluation
                        selected = candidate
        else:
            if turn == self._player_clr:
                return self.min_max(
                    black_board, white_board, turn^1, depth-1, max_evaluation,
                    )
            else:
                return self.min_max(
                    black_board, white_board, turn^1, depth-1, min_evaluation,
                    )
        if turn == self._player_clr:
            return max_evaluation, selected
        else:
            return min_evaluation, selected

    def put_disk(self, othello):
        black_board, white_board = othello.board.return_board()
        turn = othello.turn
        self._player_clr = turn
        self._count_pass = 0
        self._othello = othello
        return self.min_max(
            black_board, white_board, turn,
            self._depth, pre_evaluation=float("inf"))[1]
