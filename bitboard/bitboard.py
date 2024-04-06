"""
This file defines the system of Reversi.
Black disk make the first move, and white disk make the second move.
"""

# from functools import lru_cache
from logging import getLogger

logger = getLogger(__name__)


class BitBoard:

    __all__ = [
        "simulate_play", "update_board",
        "count_disks", "reversible_area", "is_reversible", "turn_playable",
        "return_board", "return_player_board", "load_board",
        ]

    BLACK = 0
    WHITE = 1
    INIT_BLACK = 0x0000000810000000
    INIT_WHITE = 0x0000001008000000

    def __init__(self):
        self._black_board = BitBoard.INIT_BLACK
        self._white_board = BitBoard.INIT_WHITE
        logger.info("Board was set.")

    @staticmethod
    def _bit_count(x: int):
        """Count the number of bit awaking.

        Parameters
        ----------
        x : int
            64-bit intager which represents the location of disk.
        """
        # Distributing by 2-bit, express the number of bits using 2-bit.
        x -= (x >> 1) & 0x5555555555555555
        # Upper 2-bit + lower 2-bit.
        x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
        # Upper 4-bit + lower 4-bit.
        x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0f
        # Upper 8-bit + lower 8-bit.
        x += x >> 8
        # Upper 16-bit + lower 16-bit.
        x += x >> 16
        # Upper 32-bit + lower 32-bit.
        x += x >> 32
        return x & 0x0000007f

    @staticmethod
    def _check_surround(put_loc: int, direction: int):
        """Check neighbor disk is reversible or not.

        Parameters
        ----------
        put_loc : int
            64-bit intager which represents the location of disk.
        direction : int
            Intager from 0 to 7.
        """
        if direction == 0:  # Upper
            return (put_loc << 8) & 0xffffffffffffff00
        elif direction == 1:  # Upper right
            return (put_loc << 7) & 0x7f7f7f7f7f7f7f00
        elif direction == 2:  # Right
            return (put_loc >> 1) & 0x7f7f7f7f7f7f7f7f
        elif direction == 3:  # Lower right
            return (put_loc >> 9) & 0x007f7f7f7f7f7f7f
        elif direction == 4:  # Lower
            return (put_loc >> 8) & 0x00ffffffffffffff
        elif direction == 5:  # Lower left
            return (put_loc >> 7) & 0x00fefefefefefefe
        elif direction == 6:  # Left
            return (put_loc << 1) & 0xfefefefefefefefe
        elif direction == 7:  # Upper left
            return (put_loc << 9) & 0xfefefefefefefe00
        else:
            raise ValueError

    def simulate_play(
            self, turn: int, put_loc: int,
            black_board: int = None, white_board: int = None,
            ):
        """Simulate the next turn.

        Parameters
        ----------
        turn : int
            If black is on turn, 1. If white, 0.
        put_loc : int
            64-bit intager which represents the location of disk.
        black_board, white_board : int
            If board is not synchronized with the instance, enter it manually.

        Returns
        -------
        reversed_black_board, reversed_white_board : list of int
        """
        if black_board is None:
            black_board = self._black_board
            white_board = self._white_board
        board = [black_board, white_board]

        # Player is board[turn].
        reverse_bit = 0
        for direction in range(8):
            reverse_bit_ = 0
            border_bit = self._check_surround(put_loc, direction)
            while border_bit & board[turn ^ 1]:
                reverse_bit_ |= border_bit
                border_bit = self._check_surround(border_bit, direction)
            # If player's disk is opposite side.
            if border_bit & board[turn]:
                reverse_bit |= reverse_bit_
        board[turn] ^= (put_loc | reverse_bit)
        board[turn ^ 1] ^= reverse_bit

        return board

    def update_board(self, black_board, white_board):
        """Put a disk and reverse opponent disks.

        Parameters
        ----------
        black_board, white_board : int
            64-bit intager.
        """
        self._black_board = black_board
        self._white_board = white_board

    def count_disks(self, black_board=None, white_board=None):
        """Returns black and white's disk number.

        Parameters
        ----------
        black_board, white_board : int (optional)
            64-bit intager.
        """
        if black_board is None:
            black_board = self._black_board
            white_board = self._white_board
        board = [black_board, white_board]
        return list(map(self._bit_count, board))

    def reversible_area(
            self, turn: int, black_board: int = None, white_board: int = None):
        """Returns reversible area.

        Parameters
        ----------
        turn : int
            If black is on turn, 1. If white, 0.
        black_board, white_board : int
            If board is not synchronized with the instance, enter it manually.

        Returns
        -------
        reversible : int
            Represents board of reversible positions.
        """
        if black_board is None:
            black_board = self._black_board
            white_board = self._white_board
        board = [black_board, white_board]
        blank_board = ~(board[0] | board[1])

        horiz_brd = board[turn ^ 1] & 0x7e7e7e7e7e7e7e7e
        vert_brd = board[turn ^ 1] & 0x00ffffffffffff00
        all_border = board[turn ^ 1] & 0x007e7e7e7e7e7e00

        # Upper
        one_rv = horiz_brd & (board[turn] << 1)
        one_rv |= horiz_brd & (one_rv << 1)
        one_rv |= horiz_brd & (one_rv << 1)
        one_rv |= horiz_brd & (one_rv << 1)
        one_rv |= horiz_brd & (one_rv << 1)
        one_rv |= horiz_brd & (one_rv << 1)
        reversible = blank_board & (one_rv << 1)

        # Lower
        one_rv = horiz_brd & (board[turn] >> 1)
        one_rv |= horiz_brd & (one_rv >> 1)
        one_rv |= horiz_brd & (one_rv >> 1)
        one_rv |= horiz_brd & (one_rv >> 1)
        one_rv |= horiz_brd & (one_rv >> 1)
        one_rv |= horiz_brd & (one_rv >> 1)
        reversible |= blank_board & (one_rv >> 1)

        # Left
        one_rv = vert_brd & (board[turn] << 8)
        one_rv |= vert_brd & (one_rv << 8)
        one_rv |= vert_brd & (one_rv << 8)
        one_rv |= vert_brd & (one_rv << 8)
        one_rv |= vert_brd & (one_rv << 8)
        one_rv |= vert_brd & (one_rv << 8)
        reversible |= blank_board & (one_rv << 8)

        # Right
        one_rv = vert_brd & (board[turn] >> 8)
        one_rv |= vert_brd & (one_rv >> 8)
        one_rv |= vert_brd & (one_rv >> 8)
        one_rv |= vert_brd & (one_rv >> 8)
        one_rv |= vert_brd & (one_rv >> 8)
        one_rv |= vert_brd & (one_rv >> 8)
        reversible |= blank_board & (one_rv >> 8)

        # Upper right
        one_rv = all_border & (board[turn] << 7)
        one_rv |= all_border & (one_rv << 7)
        one_rv |= all_border & (one_rv << 7)
        one_rv |= all_border & (one_rv << 7)
        one_rv |= all_border & (one_rv << 7)
        one_rv |= all_border & (one_rv << 7)
        reversible |= blank_board & (one_rv << 7)

        # Upper left
        one_rv = all_border & (board[turn] << 9)
        one_rv |= all_border & (one_rv << 9)
        one_rv |= all_border & (one_rv << 9)
        one_rv |= all_border & (one_rv << 9)
        one_rv |= all_border & (one_rv << 9)
        one_rv |= all_border & (one_rv << 9)
        reversible |= blank_board & (one_rv << 9)

        # Lower right
        one_rv = all_border & (board[turn] >> 9)
        one_rv |= all_border & (one_rv >> 9)
        one_rv |= all_border & (one_rv >> 9)
        one_rv |= all_border & (one_rv >> 9)
        one_rv |= all_border & (one_rv >> 9)
        one_rv |= all_border & (one_rv >> 9)
        reversible |= blank_board & (one_rv >> 9)

        # Lower left
        one_rv = all_border & (board[turn] >> 7)
        one_rv |= all_border & (one_rv >> 7)
        one_rv |= all_border & (one_rv >> 7)
        one_rv |= all_border & (one_rv >> 7)
        one_rv |= all_border & (one_rv >> 7)
        one_rv |= all_border & (one_rv >> 7)
        reversible |= blank_board & (one_rv >> 7)
        return reversible

    def is_reversible(
            self, turn: int, put_loc: int,
            black_board: int = None, white_board: int = None,
            ):
        """Return wheather you can put disk on (x,y) or not.

        Parameters
        ----------
        turn : int
            If black is on turn, 1. If white, 0.
        put_loc : int
            64-bit intager which represents the location of disk.
        black_board, white_board : int (optional)
            64-bit intager.

        Returns
        -------
        is_reversible : bool
        """
        if black_board is None:
            black_board = self._black_board
            white_board = self._white_board
        reversible = self.reversible_area(turn, black_board, white_board)
        return (put_loc & reversible) == put_loc

    def turn_playable(
            self, turn: int, black_board: int = None, white_board: int = None,
            ):
        """Return wheather you can put disk or not.

        Parameters
        ----------
        turn : int
            If black is on turn, 1. If white, 0.
        put_loc : int
            64-bit intager which represents the location of disk.
        black_board, white_board : int (optional)
            64-bit intager.
        """
        if black_board is None:
            black_board = self._black_board
            white_board = self._white_board
        reversible = self.reversible_area(turn, black_board, white_board)
        return reversible != 0

    def return_board(self):
        return self._black_board, self._white_board

    def return_player_board(self, turn: int):
        board = [self._black_board, self._white_board]
        return board[turn], board[turn ^ 1]

    def load_board(self, black_board, white_board):
        self._black_board = black_board
        self._white_board = white_board
