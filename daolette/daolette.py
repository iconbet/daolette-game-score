from iconservice import *

TAG = 'DAOLETTE'

BET_LIMIT_RATIOS = [147, 2675, 4315, 2725, 1930, 1454, 1136, 908, 738, 606,
                    500, 413, 341, 280, 227, 182, 142, 107, 76, 48, 23]
BET_MIN = 100000000000000000  # 1.0E+17, .1 ICX
BET_TYPES = ["none", "bet_on_numbers", "bet_on_color", "bet_on_even_odd", "bet_on_number", "number_factor"]
WHEEL_ORDER = ["2", "20", "3", "17", "6", "16", "7", "13", "10", "12",
               "11", "9", "14", "8", "15", "5", "18", "4", "19", "1", "0"]
WHEEL_BLACK = "2,3,6,7,10,11,14,15,18,19"
SET_BLACK = {'2', '3', '6', '7', '10', '11', '14', '15', '18', '19'}
WHEEL_RED = "1,4,5,8,9,12,13,16,17,20"
SET_RED = {'1', '4', '5', '8', '9', '12', '13', '16', '17', '20'}
WHEEL_ODD = "1,3,5,7,9,11,13,15,17,19"
SET_ODD = {'1', '3', '5', '7', '9', '11', '13', '15', '17', '19'}
WHEEL_EVEN = "2,4,6,8,10,12,14,16,18,20"
SET_EVEN = {'2', '4', '6', '8', '10', '12', '14', '16', '18', '20'}
MULTIPLIERS = {"bet_on_color": 2, "bet_on_even_odd": 2, "bet_on_number": 20, "number_factor": 20.685}

# An interface to Treasury SCORE
class TreasuryInterface(InterfaceScore):
    @interface
    def get_treasury_min(self) -> int:
        pass

    @interface
    def send_wager(self, _amount: int) -> None:
        pass

    @interface
    def wager_payout(self,_payout:int) -> None:
        pass


class Daolette(IconScoreBase):
    _GAME_ON = "game_on"
    _TREASURY_SCORE="treasury_score"

    @eventlog(indexed=2)
    def BetSource(self, _from: Address, timestamp: int):
        pass

    @eventlog(indexed=2)
    def BetPlaced(self, amount: int, numbers: str):
        pass

    @eventlog(indexed=2)
    def BetResult(self, spin: str, winningNumber: str, payout: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        Logger.debug(f'In __init__.', TAG)
        Logger.debug(f'owner is {self.owner}.', TAG)
        self._game_on = VarDB(self._GAME_ON, db, value_type=bool)
        self._treasury_score = VarDB(self._TREASURY_SCORE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()
        self._game_on.set(False)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def get_score_owner(self) -> Address:
        """
        A function to return the owner of this score.
        :return: Owner address of this score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self.owner

    @external
    def set_treasury_score(self, _score: Address) -> None:
        """
        Sets the treasury score address. The function can only be invoked by score owner.
        :param _score: Score address of the treasury
        :type _score: :class:`iconservice.base.address.Address`
        """
        if self.msg.sender == self.owner:
            self._treasury_score.set(_score)

    @external(readonly=True)
    def get_treasury_score(self) -> Address:
        """
        Returns the treasury score address.
        :return: Address of the treasury score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self._treasury_score.get()

    @external
    def game_on(self) -> None:
        """
        Set the status of game as on. Only the owner of the game can call this method. Owner must have set the
        treasury score before changing the game status as on.
        """
        if self.msg.sender != self.owner:
            revert('Only the owner can call the game_on method')
        if not self._game_on.get() and self._treasury_score.get() is not None:
            self._game_on.set(True)

    @external
    def game_off(self) -> None:
        """
        Set the status of game as off. Only the owner of the game can call this method.
        """
        if self.msg.sender != self.owner:
            revert('Only the owner can call the game_on method')
        if self._game_on.get():
            self._game_on.set(False)

    @external(readonly=True)
    def get_game_on(self) -> bool:
        """
        Returns the current game status
        :return: Current game status
        :rtype: bool
        """
        return self._game_on.get()

    @external(readonly=True)
    def get_multipliers(self) -> str:
        """
        Returns the multipliers of different bet types
        :return: Multipliers of different bet types
        :rtype: str
        """
        return str(MULTIPLIERS)

    @external(readonly=True)
    def get_bet_limit(self, n: int) -> int:
        """
        Returns the bet limit for the number of selected numbers
        :param n: No. of selected numbers
        :return: Bet limit in loop
        """
        treasury_score = self.create_interface_score(self._treasury_score.get(), TreasuryInterface)
        _treasury_min = treasury_score.get_treasury_min()
        return _treasury_min // BET_LIMIT_RATIOS[n]

    @external
    @payable
    def bet_on_numbers(self, numbers: str, user_seed: str = '') -> None:
        """
        Takes a list of numbers in the form of a comma separated string. e.g. "1,2,3,4" and user seed
        :param numbers: Numbers selected
        :type numbers: str
        :param user_seed: User seed/ Lucky phrase provided by user which is used in random number calculation
        :type user_seed: str
        :return:
        """
        numset = set(numbers.split(','))
        if numset == SET_RED or numset == SET_BLACK:
            self.__bet(numbers, user_seed, BET_TYPES[2])
        elif numset == SET_ODD or numset == SET_EVEN:
            self.__bet(numbers, user_seed, BET_TYPES[3])
        else:
            self.__bet(numbers, user_seed, BET_TYPES[1])

    @external
    @payable
    def bet_on_color(self, color: bool, user_seed: str = '') -> None:
        """
        The bet is set on either red color or black color.
        :param color: Red Color is chosen if true. Black if false
        :type color: blue
        :param user_seed: User seed/ Lucky phrase provided by user which is used in random number calculation
        :type user_seed: str
        :return:
        """
        if color:
            numbers = WHEEL_RED
        else:
            numbers = WHEEL_BLACK
        self.__bet(numbers, user_seed, BET_TYPES[2])

    @external
    @payable
    def bet_on_even_odd(self, even_odd: bool, user_seed: str = '') -> None:
        """
        The bet is set on either odd or even numbers.
        :param even_odd: Odd numbers is chosen if true. Even if false.
        :type even_odd: bool
        :param user_seed: User seed/ Lucky phrase provided by user which is used in random number calculation
        :type user_seed: str
        :return:
        """
        if even_odd:
            numbers = WHEEL_ODD
        else:
            numbers = WHEEL_EVEN
        self.__bet(numbers, user_seed, BET_TYPES[3])

    @external
    def untether(self) -> None:
        """
        A function to redefine the value of self.owner once it is possible.
        To be included through an update if it is added to IconService.
        Sets the value of self.owner to the score holding the game treasury.
        """
        if self.msg.sender != self.owner:
            revert(f'Only the owner can call the untether method.')
        pass

    def get_random(self, user_seed: str = '') -> float:
        """
        Generates a random # from tx hash, block timestamp and user provided
        seed. The block timestamp provides the source of unpredictability.
        :param user_seed: 'Lucky phrase' provided by user.
        :type user_seed: str
        :return: number from [x / 100000.0 for x in range(100000)] i.e. [0,0.99999]
        :rtype: float
        """
        Logger.debug(f'Entered get_random.', TAG)
        if self.msg.sender.is_contract:
            revert("ICONbet: SCORE cant play games")
        seed = (str(bytes.hex(self.tx.hash)) + str(self.now()) + user_seed)
        spin = (int.from_bytes(sha3_256(seed.encode()), "big") % 100000) / 100000.0
        Logger.debug(f'Result of the spin was {spin}.', TAG)
        return spin

    def __bet(self, numbers: str, user_seed: str, bet_type: str) -> None:
        """
        Takes a list of numbers in the form of a comma separated string and the user seed
        :param numbers: The numbers which are selected for the bet
        :type numbers: str
        :param user_seed: User seed/ Lucky phrase provided by user which is used in random number calculation
        :type user_seed: str
        :return:
        """
        self.BetSource(self.tx.origin, self.tx.timestamp)

        treasury_score=self.create_interface_score(self._treasury_score.get(),TreasuryInterface)
        _treasury_min=treasury_score.get_treasury_min()
        if not self._game_on.get():
            Logger.debug(f'Game not active yet.', TAG)
            revert(f'Game not active yet.')
        amount = self.msg.value
        Logger.debug(f'Betting {amount} loop on {numbers}.', TAG)
        self.BetPlaced(amount, numbers)
        treasury_score.icx(self.msg.value).send_wager(amount)

        nums = set(numbers.split(','))
        n = len(nums)
        if n == 0:
            Logger.debug(f'Bet placed without numbers.', TAG)
            revert(f' Invalid bet. No numbers submitted. Zero win chance. Returning funds.')
        elif n > 20:
            Logger.debug(f'Bet placed with too many numbers. Max numbers = 20.', TAG)
            revert(f' Invalid bet. Too many numbers submitted. Returning funds.')

        numset = set(WHEEL_ORDER)
        numset.remove('0')
        for num in nums:
            if num not in numset:
                Logger.debug(f'Invalid number submitted.', TAG)
                revert(f' Please check your bet. Numbers must be between 0 and 20, submitted as a comma separated '
                       f'string. Returning funds.')

        if bet_type == BET_TYPES[2] or bet_type == BET_TYPES[3]:
            bet_limit = _treasury_min // BET_LIMIT_RATIOS[0]
        else:
            bet_limit = _treasury_min // BET_LIMIT_RATIOS[n]
        if amount < BET_MIN or amount > bet_limit:
            Logger.debug(f'Betting amount {amount} out of range.', TAG)
            revert(f'Betting amount {amount} out of range ({BET_MIN} -> {bet_limit} loop).')

        if n == 1:
            bet_type = BET_TYPES[4]
        if bet_type == BET_TYPES[1]:
            payout = int(MULTIPLIERS[BET_TYPES[5]] * 1000) * amount // (1000 * n)
        else:
            payout = MULTIPLIERS[bet_type] * amount
        if self.icx.get_balance(self._treasury_score.get()) < payout:
            Logger.debug(f'Not enough in treasury to make the play.', TAG)
            revert('Not enough in treasury to make the play.')

        spin = self.get_random(user_seed)
        winningNumber = WHEEL_ORDER[int(spin * 21)]
        Logger.debug(f'winningNumber was {winningNumber}.', TAG)
        win = winningNumber in nums
        payout = payout * win
        self.BetResult(str(spin), winningNumber, payout)

        if win == 1:
            Logger.debug(f'Won',TAG)
            treasury_score.wager_payout(payout)
        else:
            Logger.debug(f'Player lost. ICX retained in treasury.', TAG)

    @payable
    def fallback(self):
        revert(f"{self.address}: This contract can't receive plain ICX")