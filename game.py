"""
File responsible for the mechanics of the game.
"""
from typing import List, Optional, Tuple
from random import randint


COMBO_TABLE = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5]
ATTACK_TABLE = [0, 1, 2, 4, 0, 2, 4, 6, 10]
B2B_BONUS = 1


class TetrominoGame:
    """An instance of TetrominoGame

    Each value in the queue is a letter representing a different piece corresponding
    with the shape of the piece: i, o, t, j, l, s, z

    These same values will be stored in the board along with '' representing nothing
    and 'g' representing gray garbage

    Instance Attributes:
        - board: a 40 length list of 10 length lists representing a 40 tall 10 wide board,
        only the first 20 rows are shown and the top 20 are hidden but still stored
        - queue: the piece queue of the current game
        - queue_position: the piece in the queue the game is at
        - current_combo: the number of consecutive block placements that have resulted
        in line clears - 1
        - back_to_back: whether the previous line clear was a t-spin or 4-line clear
        - piece_position: the current piece position represented by a list of two ints where the
        first value is the y-position and the second value is the x-position
        - piece_orientation: a value from 0 to 3 representing the current piece orientation
        where 0 is the default and a clockwise rotation advances the orientation by 1
        - hold: whether the player can hold the current piece
        - held: the current piece held in hold
        - prev_held: the previously held piece
        - held_index: the index of the held piece
        - sent_garbage: a list of garbage to be sent to the other player, is cleared after sent
        - total_attack: the total attack
        - pending_garbage: a list of pending garbage, cleared after received
        - previous_action: the previous change be it rotation, hard drop, etc. for t-spin detection
        - game_over: whether the game is over or not

    Representation Invariants:
        - len(self.board) == 40
        - all(len(row) == 10 for row in self.board)
        - all(all(value in ('i', 'j', 'l', 's', 'z', 'o', 't', 'g', '') for value in row)
        for row in self.board)
        - all(piece in ('i', 'j', 'l', 's', 'z', 'o', 't') for piece in self.queue)
        - 0 <= self.piece_position < len(self.queue)
        - self.current_combo >= -1
        - 0 <= self.piece_position[0] <= 39
        - 0 <= self.piece_position[0] <= 9
        - self.piece_orientation in (0, 1, 2, 3)
        - self.held in ('i', 'j', 'l', 's', 'z', 'o', 't', '')
        - -1 <= self.held_index <= self.queue_position
        - self.prev_held in ('i', 'j', 'l', 's', 'z', 'o', 't', '')
        - all(type(value) is int for value in self.sent_garbage)
        - all(type(value) is int for value in self.pending_garbage)
    """
    board: list
    queue: list
    queue_position: int
    current_combo: int
    back_to_back: bool
    piece_position: list
    piece_orientation: int
    hold: bool
    held: str
    prev_held: str
    held_index: int
    sent_garbage: list
    total_attack: int
    pending_garbage: list
    previous_action: str
    game_over: bool

    def __init__(self, queue: List[str]) -> None:
        """Initialize a new TetrominoGame"""
        self.board = [['' for _ in range(0, 10)] for _ in range(0, 40)]
        self.queue = queue.copy()
        self.queue_position = -1
        self.current_combo = -1
        self.back_to_back = False
        self.hold = False
        self.held = ''
        self.held_index = -1
        self.prev_held = ''
        self.sent_garbage = []
        self.pending_garbage = []
        self.previous_action = ''
        self.game_over = False
        self.next_piece()
        self.total_attack = 0

    def get_piece(self, pos: int) -> str:
        """Returns a piece where 0 is the current piece, 1 is the next piece, etc."""
        if self.hold is False or pos != 0:
            return self.queue[self.queue_position + pos]
        elif self.held_index + 1 == self.queue_position:
            return self.queue[self.queue_position + pos]
        else:
            return self.prev_held

    def next_piece(self) -> None:
        """Advances the queue by 1 and spawns the next piece"""
        self.queue_position += 1
        self.piece_position = [19, 4]
        self.piece_orientation = 0
        filled = get_filled(self.get_piece(0), self.piece_position, self.piece_orientation)
        if any(self.board[p[0]][p[1]] != '' for p in filled):
            self.game_over = True
        for pos in filled:
            self.board[pos[0]][pos[1]] = self.get_piece(0)

    def change_board(self, new_pos: List[int], new_orientation: int) -> None:
        """Erases the current position and fills in the new position"""
        piece = self.get_piece(0)
        current = get_filled(piece, self.piece_position, self.piece_orientation)
        for pos in current:
            self.board[pos[0]][pos[1]] = ''
        new = get_filled(piece, new_pos, new_orientation)
        for pos in new:
            self.board[pos[0]][pos[1]] = piece

    def move_left(self) -> str:
        """Try to move the current piece left one cell. If the piece is blocked or the piece
        would be in an invalid position, do nothing. If the piece is moved, return 'moved'.
        If not, return 'not moved'.
        """
        piece = self.get_piece(0)
        current = get_filled(piece, self.piece_position, self.piece_orientation)
        tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1],
                           self.piece_orientation)
        if tiled is not None:
            if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                self.change_board([self.piece_position[0], self.piece_position[1] - 1],
                                  self.piece_orientation)
                self.piece_orientation = self.piece_orientation
                self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                self.previous_action = 'move'
                return 'moved'
        return 'not moved'

    def das_left(self) -> None:
        """Try to move the current piece left all the way"""
        for _ in range(0, 10):
            move = self.move_left()
            if move == 'not moved':
                return

    def move_right(self) -> str:
        """Try to move the current piece right one cell. If the piece is blocked or the piece
        would be in an invalid position, do nothing. If the piece is moved, return 'moved'.
        If not, return 'not moved'.
        """
        piece = self.get_piece(0)
        current = get_filled(piece, self.piece_position, self.piece_orientation)
        tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1],
                           self.piece_orientation)
        if tiled is not None:
            if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                self.change_board([self.piece_position[0], self.piece_position[1] + 1],
                                  self.piece_orientation)
                self.piece_orientation = self.piece_orientation
                self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                self.previous_action = 'move'
                return 'moved'
        return 'not moved'

    def das_right(self) -> None:
        """Try to move the current piece right all the way"""
        for _ in range(0, 10):
            move = self.move_right()
            if move == 'not moved':
                return

    def hold_piece(self) -> None:
        """Try to hold the current piece."""
        if self.hold is False:
            # erase current piece
            current = get_filled(self.get_piece(0), self.piece_position,
                                 self.piece_orientation)
            for pos in current:
                self.board[pos[0]][pos[1]] = ''
            # hold piece
            if self.held == '':
                self.held = self.queue[self.queue_position]
                self.held_index = self.queue_position
                self.next_piece()
                self.hold = True
            else:
                self.prev_held = self.held
                self.hold = True
                self.next_piece()
                self.queue_position -= 1
                self.held = self.queue[self.queue_position]
                self.held_index = self.queue_position

    def move_down(self) -> str:
        """Try to move the current piece down one cell. If the piece is blocked or the piece
        would be in an invalid position, do nothing. If the piece is moved, return 'moved'.
        If not, return 'not moved'.
        """
        piece = self.get_piece(0)
        current = get_filled(piece, self.piece_position, self.piece_orientation)
        tiled = get_filled(piece, [self.piece_position[0] - 1, self.piece_position[1]],
                           self.piece_orientation)
        if tiled is not None:
            if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                self.change_board([self.piece_position[0] - 1, self.piece_position[1]],
                                  self.piece_orientation)
                self.piece_orientation = self.piece_orientation
                self.piece_position = [self.piece_position[0] - 1, self.piece_position[1]]
                self.previous_action = 'move'
                return 'moved'
        return 'not moved'

    def hard_drop(self) -> None:
        """Move the piece as far down as possible and then lock the piece"""
        self.soft_drop()
        self.lock_piece()

    def soft_drop(self) -> None:
        """Move the piece as far down as possible without locking the piece"""
        for _ in range(0, 40):
            move = self.move_down()
            if move == 'not moved':
                return

    def accept_pending(self, no_lines: int) -> None:
        """Accept one pending attack by adding a garbage layer to the bottom of the board.
        A garbage layer is identified by the presence of cells in the board containing
        a 'g' for garbage. A garbage row is a full row of 'g's in the board with one empty cell
        in the row determined randomly. This empty row is the same row for all of the same attack.
        """
        garbage = ['g' for x in range(0, 10)]
        random = randint(0, 9)
        garbage[random] = ''
        for _ in range(0, no_lines):
            self.board.insert(0, garbage.copy())
            self.board.pop()

    def lock_piece(self) -> Tuple[int, List[int], int]:
        """Lock the current piece and check for line clears and t-spin. Return a tuple of
        the raw attack, tiled rows, and the value of the kind of clear in the attack table.
        If nothing is cleared, the third value (the value identifying the kind of clear) is -1.
        """
        self.hold = False
        raw_attack = 0
        placement_type = -1
        # check spin
        spin = 'no'
        if self.get_piece(0) == 't':
            spin = self.check_t_spin()

        tiled = self.check_tiled()
        if tiled == []:
            self.current_combo = -1
            while self.pending_garbage != []:
                next_garbage = self.pending_garbage.pop(0)
                self.accept_pending(next_garbage)
        else:
            # add up attack
            attack = 0

            # add b2b bonus
            if len(tiled) == 4 or spin == 't' or spin == 'mini':
                if self.back_to_back is True:
                    if spin != 'mini' or len(tiled) >= 2:
                        attack += B2B_BONUS
                else:
                    self.back_to_back = True
            else:
                self.back_to_back = False

            # add attack based on type of clear and number of lines cleared
            if spin == 't' or (spin == 'mini' and len(tiled) >= 2):
                attack += ATTACK_TABLE[len(tiled) + 4]
                placement_type = len(tiled) + 4
            elif spin == 'mini':
                attack += ATTACK_TABLE[4]
                placement_type = 4
            else:
                attack += ATTACK_TABLE[len(tiled) - 1]
                placement_type = len(tiled) - 1

            # add attack based on combo
            self.current_combo += 1
            attack += COMBO_TABLE[min(self.current_combo, 12)]

            # remove tiled rows
            for i in range(0, len(tiled)):
                self.board.pop(tiled[len(tiled) - i - 1])
                self.board.append(['' for _ in range(0, 10)])

            # check for all clear
            if all(all(item == '' for item in row) for row in self.board):
                attack = ATTACK_TABLE[8]
                placement_type = 8

            raw_attack = attack

            # garbage cancelling
            while attack != 0 and self.pending_garbage != []:
                if self.pending_garbage[0] <= attack:
                    garbage = self.pending_garbage.pop(0)
                    attack -= garbage
                else:
                    self.pending_garbage[0] -= attack

            # add to sent garbage
            if attack != 0:
                self.sent_garbage.append(attack)

        self.previous_action = 'lock'
        self.next_piece()
        self.total_attack += raw_attack
        return (raw_attack, tiled, placement_type)

    def check_tiled(self) -> List[int]:
        """Check which rows are fully filled and return a list of the positions that are."""
        tiled = []

        # check only around the current piece position for clears
        for i in range(self.piece_position[0] - 3, self.piece_position[0] + 4):
            if all(value != '' for value in self.board[i]):
                tiled.append(i)
        return tiled

    def check_t_spin(self) -> str:
        """Check for a t-spin or t-spin mini.
        Returns 't', 'mini', or 'no' depending on the type of spin
        """
        if self.previous_action != 'rotate':
            return 'no'

        # t-piece is at left wall
        if self.piece_position[1] == 0:
            if self.board[self.piece_position[0] - 1][self.piece_position[1] + 1] != '' \
                    and self.board[self.piece_position[0] + 1][self.piece_position[1] + 1] != '':
                return 't'
            elif self.board[self.piece_position[0] - 1][self.piece_position[1] + 1] != '' \
                    or self.board[self.piece_position[0] + 1][self.piece_position[1] + 1] != '':
                return 'mini'
            else:
                return 'no'

        # t-piece is at right wall
        if self.piece_position[1] == 9:
            if self.board[self.piece_position[0] - 1][self.piece_position[1] - 1] != '' \
                    and self.board[self.piece_position[0] + 1][self.piece_position[1] - 1] != '':
                return 't'
            elif self.board[self.piece_position[0] - 1][self.piece_position[1] - 1] != '' \
                    or self.board[self.piece_position[0] + 1][self.piece_position[1] - 1] != '':
                return 'mini'
            else:
                return 'no'

        # t-piece is flat at the bottom
        if self.piece_position[0] == 0:
            if self.board[self.piece_position[0] + 1][self.piece_position[1] + 1] != '' \
                    or self.board[self.piece_position[0] + 1][self.piece_position[1] - 1] != '':
                return 'mini'
            else:
                return 'no'

        # any other case
        missing_corners = []
        if self.board[self.piece_position[0] + 1][self.piece_position[1] + 1] == '':
            missing_corners.append('tr')
        if self.board[self.piece_position[0] + 1][self.piece_position[1] - 1] == '':
            missing_corners.append('tl')
        if self.board[self.piece_position[0] - 1][self.piece_position[1] + 1] == '':
            missing_corners.append('br')
        if self.board[self.piece_position[0] - 1][self.piece_position[1] - 1] == '':
            missing_corners.append('bl')

        # missing more than one corner means it is not a 't' or mini' kind of spin
        if len(missing_corners) > 1:
            return 'no'

        # if the middle part of the T has a missing corner on either side, it is a 'mini'
        if self.piece_orientation == 0 and ('tr' in missing_corners or 'tl' in missing_corners):
            return 'mini'
        if self.piece_orientation == 1 and ('tr' in missing_corners or 'br' in missing_corners):
            return 'mini'
        if self.piece_orientation == 2 and ('bl' in missing_corners or 'br' in missing_corners):
            return 'mini'
        if self.piece_orientation == 3 and ('bl' in missing_corners or 'tl' in missing_corners):
            return 'mini'

        # otherwise it is a t-spin
        return 't'

    def get_app(self) -> float:
        """Returns the attack per piece (APP) used of the game"""
        if self.queue_position != 0:
            return self.total_attack / self.queue_position
        else:
            return 0

    def rotate_cw(self) -> None:
        """Rotate the current piece clockwise, if possible. First check the rotation about the
        centre of the piece. If the rotation is not possible, kick the piece into other
        position until the rotation works or until running out of possible kicks. In that case,
        do not rotate the piece.
        """
        piece = self.get_piece(0)
        current = get_filled(piece, self.piece_position, self.piece_orientation)

        # kick table is the same for ljtsz
        if piece not in ('o', 'i'):
            if self.piece_orientation == 0:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2, self.piece_position[1]], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2, self.piece_position[1]], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] - 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 1:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2, self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2, self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] + 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] + 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 2:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2, self.piece_position[1]], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2, self.piece_position[1]], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 3:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2, self.piece_position[1]], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2, self.piece_position[1]], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] - 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] - 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                return

        # different kick table for i
        if piece == 'i':
            if self.piece_orientation == 0:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 2], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 2], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] + 2], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] + 2], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 1:
                tiled = get_filled(piece, [self.piece_position[0] - 1, self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1, self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] + 2], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] + 2], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] + 2], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] + 2], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 2:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 2], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 2], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] - 2], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] - 2], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 3:
                tiled = get_filled(piece, [self.piece_position[0] + 1, self.piece_position[1]], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1, self.piece_position[1]], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 1, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] - 2], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] - 2], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] - 2], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] - 2], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                return

    def rotate_ccw(self) -> None:
        """Rotate the current piece counterclockwise, if possible. First check the rotation about
        the centre of the piece. If the rotation is not possible, kick the piece into other
        position until the rotation works or until running out of possible kicks. In that case,
        do not rotate the piece. """
        piece = self.get_piece(0)
        current = get_filled(piece, self.piece_position, self.piece_orientation)

        # kick table is the same for ljtsz
        if piece not in ('o', 'i'):
            if self.piece_orientation == 0:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2, self.piece_position[1]], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2, self.piece_position[1]], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] + 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] + 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 3:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2, self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2, self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] - 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] - 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 2:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2, self.piece_position[1]], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2, self.piece_position[1]], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] - 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] - 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] - 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 1:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1]], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1]], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2, self.piece_position[1]], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2, self.piece_position[1]], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                return
        # different kick table for i
        if piece == 'i':
            if self.piece_orientation == 0:
                tiled = get_filled(piece, [self.piece_position[0] - 1, self.piece_position[1]], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1, self.piece_position[1]], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 1, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] + 2], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] + 2], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] - 1], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] + 2], 3)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] + 2], 3)
                        self.piece_orientation = 3
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 3:
                tiled = get_filled(piece, [self.piece_position[0] + 1, self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1, self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 1, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1, self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1, self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2, self.piece_position[1]], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2, self.piece_position[1]], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 2, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] - 1], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] + 2], 2)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] + 2], 2)
                        self.piece_orientation = 2
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] + 2]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 2:
                tiled = get_filled(piece, [self.piece_position[0] + 1, self.piece_position[1]], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1, self.piece_position[1]], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 1, self.piece_position[1]]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] - 2], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] - 2], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 1,
                                           self.piece_position[1] + 1], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] - 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 2,
                                           self.piece_position[1] - 2], 1)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 2,
                                           self.piece_position[1] - 2], 1)
                        self.piece_orientation = 1
                        self.piece_position = [self.piece_position[0] + 2,
                                               self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                return
            if self.piece_orientation == 1:
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0], self.piece_position[1] - 2], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0], self.piece_position[1] - 2], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0], self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] + 1,
                                           self.piece_position[1] + 1], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] + 1,
                                               self.piece_position[1] + 1]
                        self.previous_action = 'rotate'
                        return
                tiled = get_filled(piece, [self.piece_position[0] - 2,
                                           self.piece_position[1] - 2], 0)
                if tiled is not None:
                    if all(self.board[pos[0]][pos[1]] == '' or pos in current for pos in tiled):
                        self.change_board([self.piece_position[0] - 2,
                                           self.piece_position[1] - 2], 0)
                        self.piece_orientation = 0
                        self.piece_position = [self.piece_position[0] - 2,
                                               self.piece_position[1] - 2]
                        self.previous_action = 'rotate'
                        return
                return


def get_filled(piece: str, position: List[int], orientation: int) -> Optional[List[List[int]]]:
    """Return the list of coordinates for given piece. Return None if invalid position

    Position is a list [y, x].
    """
    if piece not in ('o', 'i'):
        if orientation == 0 and (position[0] <= -1 or position[1] <= 0 or position[1] >= 9):
            return None
        if orientation == 1 and (position[0] <= 0 or position[1] <= -1 or position[1] >= 9):
            return None
        if orientation == 2 and (position[0] <= 0 or position[1] <= 0 or position[1] >= 9):
            return None
        if orientation == 3 and (position[0] <= 0 or position[1] <= 0 or position[1] >= 10):
            return None
    if piece == 'l':
        if orientation == 0:
            return [[position[0], position[1] - 1], [position[0], position[1]],
                    [position[0], position[1] + 1], [position[0] + 1, position[1] + 1]]
        if orientation == 1:
            return [[position[0] + 1, position[1]], [position[0], position[1]],
                    [position[0] - 1, position[1]], [position[0] - 1, position[1] + 1]]
        if orientation == 2:
            return [[position[0] - 1, position[1] - 1], [position[0], position[1] - 1],
                    [position[0], position[1]], [position[0], position[1] + 1]]
        if orientation == 3:
            return [[position[0] + 1, position[1] - 1], [position[0] + 1, position[1]],
                    [position[0], position[1]], [position[0] - 1, position[1]]]
    if piece == 'j':
        if orientation == 0:
            return [[position[0], position[1] - 1], [position[0], position[1]],
                    [position[0], position[1] + 1], [position[0] + 1, position[1] - 1]]
        if orientation == 1:
            return [[position[0] + 1, position[1]], [position[0], position[1]],
                    [position[0] - 1, position[1]], [position[0] + 1, position[1] + 1]]
        if orientation == 2:
            return [[position[0] - 1, position[1] + 1], [position[0], position[1] - 1],
                    [position[0], position[1]], [position[0], position[1] + 1]]
        if orientation == 3:
            return [[position[0] - 1, position[1] - 1], [position[0] + 1, position[1]],
                    [position[0], position[1]], [position[0] - 1, position[1]]]
    if piece == 't':
        if orientation == 0:
            return [[position[0], position[1] - 1], [position[0], position[1]],
                    [position[0], position[1] + 1], [position[0] + 1, position[1]]]
        if orientation == 1:
            return [[position[0] + 1, position[1]], [position[0], position[1]],
                    [position[0] - 1, position[1]], [position[0], position[1] + 1]]
        if orientation == 2:
            return [[position[0], position[1] - 1], [position[0], position[1]],
                    [position[0], position[1] + 1], [position[0] - 1, position[1]]]
        if orientation == 3:
            return [[position[0] - 1, position[1]], [position[0], position[1]],
                    [position[0] + 1, position[1]], [position[0], position[1] - 1]]
    if piece == 's':
        if orientation == 0:
            return [[position[0], position[1] - 1], [position[0], position[1]],
                    [position[0] + 1, position[1]], [position[0] + 1, position[1] + 1]]
        if orientation == 1:
            return [[position[0] + 1, position[1]], [position[0], position[1] + 1],
                    [position[0], position[1]], [position[0] - 1, position[1] + 1]]
        if orientation == 2:
            return [[position[0], position[1] + 1], [position[0], position[1]],
                    [position[0] - 1, position[1]], [position[0] - 1, position[1] - 1]]
        if orientation == 3:
            return [[position[0] + 1, position[1] - 1], [position[0], position[1] - 1],
                    [position[0], position[1]], [position[0] - 1, position[1]]]
    if piece == 'z':
        if orientation == 0:
            return [[position[0] + 1, position[1] - 1], [position[0] + 1, position[1]],
                    [position[0], position[1]], [position[0], position[1] + 1]]
        if orientation == 1:
            return [[position[0] + 1, position[1] + 1], [position[0], position[1] + 1],
                    [position[0], position[1]], [position[0] - 1, position[1]]]
        if orientation == 2:
            return [[position[0], position[1] - 1], [position[0] - 1, position[1]],
                    [position[0], position[1]], [position[0] - 1, position[1] + 1]]
        if orientation == 3:
            return [[position[0] + 1, position[1]], [position[0], position[1] - 1],
                    [position[0], position[1]], [position[0] - 1, position[1] - 1]]
    if piece == 'o':
        if position[1] >= 9 or position[1] <= -1:
            return None
        if position[0] <= -1:
            return None
        return [[position[0], position[1] + 1], [position[0] + 1, position[1]],
                [position[0], position[1]], [position[0] + 1, position[1] + 1]]
    if piece == 'i':
        if orientation == 0 and (position[1] <= 0 or position[1] >= 8 or position[0] <= -1):
            return None
        if orientation == 2 and (position[1] <= 1 or position[1] >= 9 or position[0] <= -1):
            return None
        if orientation == 1 and (position[1] <= -1 or position[1] >= 10 or position[0] <= 1):
            return None
        if orientation == 3 and (position[1] <= -1 or position[1] >= 10 or position[0] <= 0):
            return None
        if orientation == 0:
            return [[position[0], position[1] - 1], [position[0], position[1]],
                    [position[0], position[1] + 1], [position[0], position[1] + 2]]
        if orientation == 1:
            return [[position[0] + 1, position[1]], [position[0], position[1]],
                    [position[0] - 1, position[1]], [position[0] - 2, position[1]]]
        if orientation == 2:
            return [[position[0], position[1] - 2], [position[0], position[1] - 1],
                    [position[0], position[1]], [position[0], position[1] + 1]]
        if orientation == 3:
            return [[position[0] + 2, position[1]], [position[0] + 1, position[1]],
                    [position[0], position[1]], [position[0] - 1, position[1]]]
    return None


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta.contracts
    python_ta.contracts.check_all_contracts()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['typing', 'random'],  # the names (strs) of imported modules
        'allowed-io': [],  # the names (strs) of functions that call print/open/input
        'max-line-length': 100,
        'disable': ['E1136', 'R0902', 'R1702', 'R0912', 'R0915'],
        'max-nested-blocks': 4
    })
