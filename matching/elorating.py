"""Calculate rating."""

import pickle


class EloRating:
    """Load and update Rating."""
    INIT_RATING = 1500
    K = 16

    def __init__(self, members, filename="./matching/strategy_rating.pkl"):
        self._filename = filename
        try:
            with open(filename, "rb") as file_:
                self._rating = pickle.load(file_)
        except FileNotFoundError:
            self._rating = {}
        for member in members:
            if member not in self._rating:
                self._rating[member] = EloRating.INIT_RATING

    def save_rating(self):
        with open(self._filename, "wb") as file_:
            pickle.dump(self._rating, file_)

    def win_lose_ratio(self, member1: str, member2: str):
        """Calculate ratio in which member1 wins."""
        rate_difference = self._rating[member2]-self._rating[member1]
        ratio = 1/(pow(10, rate_difference/400)+1)
        return ratio

    def update_rating(
            self, member1: str, member2: str,
            number_game: int, cnt_mbr1_win: int,
            ):
        """Update rating.

        Parameters
        ----------
        member1, member2 : str
            Names of used members.

        number_game : int
            Number of matches.

        cnt_mbr1_win : int
            Number of the matches member1 won.
        """
        cnt_mbr2_win = number_game - cnt_mbr1_win
        pre_prblty_1 = self.win_lose_ratio(member1, member2)
        expected_win_1 = pre_prblty_1 * number_game
        pre_prblty_2 = self.win_lose_ratio(member2, member1)
        expected_win_2 = pre_prblty_2 * number_game

        self._rating[member1] = (
            self._rating[member1]
            + EloRating.K * (cnt_mbr1_win - expected_win_1)
        )
        self._rating[member2] = (
            self._rating[member2]
            + EloRating.K * (cnt_mbr2_win - expected_win_2)
        )

    def initialize_rating(self):
        for member in self._rating.keys():
            self._rating[member] = EloRating.INIT_RATING
