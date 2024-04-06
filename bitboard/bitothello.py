"""Python de Othello"""

import copy
from collections import deque
from logging import getLogger
import random

from .bitboard import BitBoard

logger = getLogger(__name__)


class OthelloGame:

    BLACK = BitBoard().BLACK
    WHITE = BitBoard().WHITE

    def __init__(self, player_clr="black"):
        # Set a board.
        self.board = BitBoard()

        # Black or white.
        if player_clr == "black":
            self._player_clr = OthelloGame.BLACK
        elif player_clr == "white":
            self._player_clr = OthelloGame.WHITE
        elif player_clr == "random":
            self._player_clr = random.choice([0, 1])
        else:
            raise KeyError

        # States of game.
        self.turn = 0
        self.reversible = 0
        self.result = "start"

        # Counter.
        self._disk_count = [2, 2]
        self._pass_cnt = [0, 0]  # [white, black]

        # Mode.
        self._player_auto = False
        logger.info("Game starts.")

        # Logger.
        self._board_log = deque([])
        self._board_back = deque([])

    def play_turn(self, put_loc: int):
        """You can put disk and reverse opponent's disk.

        Parameters
        ----------
        put_loc : int
            Integer from 0 to 63.
        """
        if not (0 <= put_loc <= 63):
            raise AssertionError
        put_loc = pow(2, put_loc)

        # If input value is not valid, raise an error.
        if not self.board.is_reversible(self.turn, put_loc):
            raise ValueError

        next_board = self.board.simulate_play(self.turn, put_loc)

        if self._player_clr == self.turn:
            # Delete roll back log which is no longer used.
            if self._board_back:
                self._board_back = deque([])
            self._board_log.append(next_board)

        # Update boards.
        self.board.update_board(*next_board)
        self._pass_cnt[self.turn] = 0
        self.turn ^= 1

    def update_count(self):
        """Update counts of disks."""
        count_board = self.board.count_disks()
        player_cpu = [
            count_board[self._player_clr],
            count_board[self._player_clr ^ 1],
        ]
        self._disk_count = player_cpu
        return player_cpu

    def judge_game(self, disk_count: list = None):
        """Judgement of game."""
        if disk_count is None:
            disk_count = self._disk_count

        # if self._pass_cnt >= 2 or sum(disk_count) == 64:
        black = self.board.reversible_area(0)
        white = self.board.reversible_area(1)
        if (black == 0 and white == 0) or sum(disk_count) == 64:
            if disk_count[0] == disk_count[1]:
                self.result = "DRAW"
            if disk_count[0] > disk_count[1]:
                self.result = "WIN"
            if disk_count[0] < disk_count[1]:
                self.result = "LOSE"
            return True
        return False

    def auto_mode(self, automode: bool = True):
        """If True is selected, the match will be played between the CPUs."""
        self._player_auto = automode

    def load_strategy(self, Strategy):
        """Set strategy class."""
        self._strategy_player = Strategy(self)
        self._strategy_opponent = Strategy(self)

    def change_strategy(self, strategy, is_player=False):
        """You can select AI strategy from candidates below.

        Parameters
        ----------
        strategy : str
            random : Put disk randomly.
            maximize : Put disk to maximize number of one's disks.
            minimize : Put disk to minimize number of one's disks.
        is_player : bool
            Default is False.
        """
        if is_player:
            self._strategy_player.set_strategy(strategy)
        else:
            self._strategy_opponent.set_strategy(strategy)

    def process_game(self):
        """
        Returns
        -------
        finished, updated : bool
        """
        self.update_count()

        if self.judge_game():
            logger.debug("Game was judged as the end.")
            return True, True

        if self.turn == self._player_clr:
            self.reversible = self.board.reversible_area(self.turn)
            if self.board.turn_playable(self.turn):
                if self._player_auto:
                    logger.debug("Player's turn was processed automatically.")
                    self.play_turn(self._strategy_player.selecter(self))
                    return False, True
                else:
                    pass
            else:
                logger.debug("Player's turn was passed.")
                self.turn ^= 1
                self._pass_cnt[self.turn] += 1
        else:
            self.reversible = self.board.reversible_area(self.turn)
            if self.board.turn_playable(self.turn):
                logger.debug("CPU's turn was processed automatically.")
                self.play_turn(self._strategy_opponent.selecter(self))
                return False, True
            else:
                logger.debug("CPU's turn was passed.")
                self.turn ^= 1
                self._pass_cnt[self.turn] += 1
        return False, False

    def display_board(self):
        """Calculate 2-dimensional arrays to be used for board display."""
        black_board, white_board = self.board.return_board()
        board_list = [[0 for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for column in range(8):
                if black_board & 1:
                    board_list[row][column] = 1
                if white_board & 1:
                    board_list[row][column] = -1
                black_board = black_board >> 1
                white_board = white_board >> 1
        return board_list

    def undo_turn(self):
        logger.debug(
            "Log:%s - %s" % (
                ", ".join(map(str, self._board_log)),
                ", ".join(map(str, self._board_back)),
                ))
        if not self._board_log:
            logger.warning("The board can not be playbacked.")
            return False

        logger.info("The board was playbacked.")
        previous_board = self._board_log.pop()
        self._board_back.append(self.board.return_board())
        self.board.load_board(*previous_board)

        logger.debug(
            "Log:%s - %s" % (
                ", ".join(map(str, self._board_log)),
                ", ".join(map(str, self._board_back)),
                ))
        return True

    def redo_turn(self):
        logger.debug(
            "Log:%s - %s" % (
                ", ".join(map(str, self._board_log)),
                ", ".join(map(str, self._board_back)),
                ))
        if not self._board_back:
            logger.warning("The board can not be advanced.")
            return False
        logger.info("The board was advanced.")
        next_board = self._board_back.pop()
        self._board_log.append(self.board.return_board())
        self.board.load_board(*next_board)
        logger.debug(
            "Log:%s - %s" % (
                ", ".join(map(str, self._board_log)),
                ", ".join(map(str, self._board_back)),
                ))
        return True

    def return_turn(self):
        return self._player_clr

    def return_state(self):
        black_board, white_board = self.board.return_board()
        return black_board, white_board, self._board_log, self._board_back

    def load_state(self, black_board, white_board, board_log, board_back):
        self.board.load_board(black_board, white_board)
        self._board_log = copy.deepcopy(board_log)
        self._board_back = copy.deepcopy(board_back)
