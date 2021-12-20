"""
File for evaluating board positions and using a tree-based AI to play the game
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from copy import deepcopy
from game import TetrominoGame, get_filled


class TetrominoAI:
    """Uses a GameTree to play the game

    Instance Attributes:
        - game: the TetrominoGame instance that the AI is playing
        - tree: the GameTree that the AI uses to pick its moves
        - max_height: limits the maximum height of the tree
        - best_n: limits the number of subtrees to recurse on to the best n subtrees
        - weights: the weights for the heuristics used to evaluate the piece placements

    Representation Invariants:
        - self.max_height >= 2
        - self.best_n >= 1
    """
    game: TetrominoGame
    tree: GameTree
    max_height: int
    best_n: int
    weights: list

    def __init__(self, game: TetrominoGame, max_height: int, best_n: int,
                 weights: List[float]) -> None:
        """Initialize a new TetrominoAI instance"""
        self.game = game
        self.max_height = max_height
        self.best_n = best_n
        self.weights = weights
        self.tree = GameTree(self.game, [], self.max_height, self.best_n, self.weights)

    def generate_tree(self) -> None:
        """Generate the subtrees of the tree and calculate the score of the subtrees"""
        # make new tree if received garbage
        if self.game.board != self.tree.game_state.board:
            self.tree = GameTree(self.game, [], self.max_height, self.best_n, self.weights)

        self.tree.generate_subtrees()
        self.tree.get_sub_score()

    def make_move(self) -> None:
        """Make a move based on the maximum sub_score of the subtrees"""
        moves = {s.sub_score: s for s in self.tree.subtrees}
        self.tree = moves[max(moves)]
        # iterate through the list of inputs and make the inputs in the list
        for i in self.tree.inputs:
            if i == 'cw':
                self.game.rotate_cw()
            elif i == 'ccw':
                self.game.rotate_ccw()
            elif i == 'left':
                self.game.move_left()
            elif i == 'right':
                self.game.move_right()
            elif i == 'hold':
                self.game.hold_piece()
        self.game.hard_drop()

        # reduce the current value to reflect the changed tree structure
        self.tree.reduce_current()


class GameTree:
    """The game tree will evaluate the board and determine the best piece placements given
    the board, the queue, and evaluation heuristics.

    Instance Attributes:
        - game_state: the TetrominoGame that the tree is evaluating
        - raw_score: the score calculated from the evaluation algorithm
        - sub_score: the score of the tree taking into account the score of its subtrees
        - inputs: the list of inputs that the tree will evaluate the score of
        - current: the current position in the full tree
        - max_height: limits the maximum height of the tree
        - best_n: limits the number of subtrees to recurse on to the best n subtrees
        - weights: the weights for the heuristics used to evaluate the piece placements

    Representation Invariants:
        - self.max_height >= 2
        - self.best_n >= 1
        - 1 <= self.current <= self.max_height
    """
    game_state: TetrominoGame
    raw_score: float
    sub_score: float
    inputs: list[str]
    current: int
    max_height: int
    best_n: int
    subtrees: list[GameTree]
    weights: list[float]

    def __init__(self, game: TetrominoGame, inputs: List[str], max_height: int,
                 best_n: int, weights: List[float], current: Optional[int] = 1) -> None:
        """Initialize a new GameTree"""
        # use same queue (not mutated) in all subtrees to speed up tree generation
        self.game_state = TetrominoGame(game.queue)

        # use deepcopy to prevent aliasing when copying the TetrominoGame
        self.game_state.queue_position = deepcopy(game.queue_position)
        self.game_state.board = deepcopy(game.board)
        self.game_state.current_combo = deepcopy(game.current_combo)
        self.game_state.back_to_back = deepcopy(game.back_to_back)
        self.game_state.hold = deepcopy(game.hold)
        self.game_state.held = deepcopy(game.held)
        self.game_state.held_index = deepcopy(game.held_index)
        self.game_state.prev_held = deepcopy(game.prev_held)
        self.game_state.pending_garbage = deepcopy(game.pending_garbage)
        self.game_state.previous_action = deepcopy(game.previous_action)

        self.inputs = inputs
        self.subtrees = []
        self.current = current
        self.max_height = max_height
        self.raw_score = 0
        self.best_n = best_n
        self.weights = weights

    def generate_subtrees(self) -> None:
        """Generate subtrees based on possible placements"""
        # generate new subtrees only if there aren't any
        if self.subtrees == []:
            # generate possible placements using possible inputs (no soft drop yet)
            piece = self.game_state.queue[self.game_state.queue_position]
            possible = get_basic_placements(piece)

            # generate possibilities with holding
            held = self.game_state.held
            possible_hold = []
            if held != '' and self.game_state.hold is False:
                possible_hold = get_basic_placements(held)
                for placement in possible_hold:
                    placement.insert(0, 'hold')
                possible.extend(possible_hold)
            if held == '':
                possible_hold = get_basic_placements(
                    self.game_state.queue[self.game_state.queue_position + 1])
                for placement in possible_hold:
                    placement.insert(0, 'hold')

            # create and evaluate subtrees using possible inputs
            for sub in possible:
                self.subtrees.append(GameTree(self.game_state, sub, self.max_height, self.best_n,
                                              self.weights, self.current + 1))
            for sub in possible_hold:
                self.subtrees.append(GameTree(self.game_state, sub, self.max_height, self.best_n,
                                              self.weights, self.current + 1))
            for s in self.subtrees:
                s.evaluate_score()

            # prune the subtrees to the best n subtrees
            n = min([self.best_n, len(self.subtrees)])
            max_n_index = list(range(0, n))
            max_n_score = [self.subtrees[j].raw_score for j in range(0, n)]
            for k in range(n, len(self.subtrees)):
                if self.subtrees[k].raw_score > min(max_n_score):
                    index = max_n_score.index(min(max_n_score))
                    max_n_index.pop(index)
                    max_n_score.pop(index)
                    max_n_index.append(k)
                    max_n_score.append(self.subtrees[k].raw_score)
            self.subtrees = [self.subtrees[i] for i in max_n_index]

        # generate subtrees of the subtrees up until a certain maximum height
        if self.current + 1 < self.max_height:
            for s in self.subtrees:
                s.generate_subtrees()

    def evaluate_score(self) -> None:
        """Calculate the score based on the weights"""
        # move and lock the piece
        self.move()
        lock = self.game_state.lock_piece()
        current = get_filled(self.game_state.queue[self.game_state.queue_position],
                             self.game_state.piece_position, self.game_state.piece_orientation)

        surface = self.get_surface(current)
        well = find_well(surface)

        # punish for rough field, do not consider the well
        no_well = surface.copy()
        no_well.pop(well[0])
        rough = roughness(no_well)
        self.raw_score += - rough * self.weights[0]

        # punish holes in the board (empty cells with a filled cell somewhere above)
        holes = self.find_holes(surface)
        self.raw_score += - holes * self.weights[1]

        # punish a high board to keep board low
        height = max(surface)
        self.raw_score += - height * self.weights[2]

        # punish height if above half of visible board to encourage downstacking a high board
        self.raw_score += - max([0, height - 10]) * self.weights[3]

        # punish height if above 3/4 of visible board to encourage downstacking a high board
        self.raw_score += - max([0, height - 15]) * self.weights[4]

        # reward a deep well
        self.raw_score += well[1] * self.weights[5]

        # reward higher attack numbers
        self.raw_score += lock[0] * self.weights[6]

        # reward combo
        self.raw_score += self.game_state.current_combo * self.weights[7]

        # punish clearing 1 or 2 lines without t-spin since little attack is sent
        if lock[2] == 0 or lock[2] == 1:
            self.raw_score += - self.weights[8]

        # reward clearing 3-4 lines at a time, t-spins, and all clears
        elif lock[2] == 2:
            self.raw_score += self.weights[9]
        elif lock[2] == 3 or lock[2] == 4 or lock[2] == 5 or lock[2] == 6 or lock[2] == 7:
            self.raw_score += self.weights[10]
        elif lock[2] == 8:
            self.raw_score += self.weights[11]

    def reduce_current(self) -> None:
        """Reduce the value of current in preparation for regenerating subtrees after making a move
        """
        for s in self.subtrees:
            s.reduce_current()
        self.current -= 1

    def get_sub_score(self) -> None:
        """Calculate the score taking into account subtrees"""
        # no subtrees than sub_score is raw_score
        if self.subtrees == []:
            self.sub_score = self.raw_score

        # calculate the sub_score of subtrees use them to calculate sub_score
        else:
            max_so_far = -999999999
            for s in self.subtrees:
                s.get_sub_score()
                if s.sub_score > max_so_far:
                    max_so_far = s.sub_score
            self.sub_score = (self.raw_score + max_so_far) / 2

    def find_holes(self, surface: List[int]) -> float:
        """Return the number of empty spaces within the stack that have a filled space above"""
        holes = 0
        for i in range(0, 10):
            for j in range(0, surface[i]):
                if self.game_state.board[j][i] == '':
                    holes += 1
        return holes

    def get_surface(self, ignore: List[List[int]]) -> List[int]:
        """Get the highest filled position of each column"""
        highest = [-1 for _ in range(0, 10)]
        for i in range(0, 40):
            row = self.game_state.board[i]
            for j in range(0, 10):
                if row[j] != '' and [i, j] not in ignore:
                    highest[j] = i
        return highest

    def move(self) -> None:
        """Make moves in inputs + soft drop"""
        for i in self.inputs:
            if i == 'cw':
                self.game_state.rotate_cw()
            elif i == 'ccw':
                self.game_state.rotate_ccw()
            elif i == 'left':
                self.game_state.move_left()
            elif i == 'right':
                self.game_state.move_right()
            elif i == 'hold':
                self.game_state.hold_piece()
        self.game_state.soft_drop()

    def _str_indented(self, depth: int) -> str:
        """Return an indented string representation of this tree's moves (inputs).

        The indentation level is specified by the depth parameter.

        Preconditions:
        - 0 <= depth
        """
        move_desc = f'{self.inputs}\n'
        text = '  ' * depth + move_desc
        if self.subtrees == []:
            return text
        else:
            for subtree in self.subtrees:
                text += subtree._str_indented(depth + 1)
            return text


def find_well(surface: List[int]) -> Tuple[int, int]:
    """Return the position of the deepest well"""
    well = 0
    deepest = surface[0]
    for i in range(1, len(surface)):
        if deepest >= surface[i]:
            well = i
    return (well, deepest)


def roughness(surface: List[int]) -> float:
    """Add the roughness of the surface which is the sum of the absolute value of the change in
    height of the top of the board given by a list representing the maximum height at each column.
    """
    sum_so_far = 0
    for i in range(0, len(surface) - 1):
        sum_so_far += abs(surface[i] - surface[i - 1])
    return sum_so_far


def get_basic_placements(piece: str) -> List[List[str]]:
    """Returns the moves for all basic piece placements. All rotations in all possible x positions
    but without soft drops."""
    if piece == 'o':
        inputs = [[]]
        for i in range(1, 5):
            inputs.append(['left'] * i)
            inputs.append(['right'] * i)
        return inputs
    elif piece == 'i':
        inputs = [[], ['cw']]
        for i in range(1, 4):
            inputs.append(['left'] * i)
            inputs.append(['right'] * i)
            inputs.append(['cw'] + ['left'] * i)
            inputs.append(['cw'] + ['right'] * i)
        inputs.append(['cw'] + ['left'] * 4)
        inputs.append(['cw'] + ['right'] * 4)
        inputs.append(['cw'] + ['left'] * 5)
        return inputs
    elif piece in ('s', 'z'):
        inputs = [[], ['cw']]
        for i in range(1, 4):
            inputs.append(['left'] * i)
            inputs.append(['right'] * i)
        inputs.append(['right'] * 4)
        for i in range(1, 5):
            inputs.append(['cw'] + ['left'] * i)
            inputs.append(['cw'] + ['right'] * i)
        return inputs
    else:   # t, l, or j
        inputs = [[], ['cw', 'cw'], ['cw'], ['ccw', 'right']]
        for i in range(1, 4):
            inputs.append(['left'] * i)
            inputs.append(['right'] * i)
            inputs.append(['cw', 'cw'] + ['left'] * i)
            inputs.append(['cw', 'cw'] + ['right'] * i)
        inputs.append(['right'] * 4)
        inputs.append(['cw', 'cw'] + ['right'] * 4)
        for i in range(1, 5):
            inputs.append(['cw'] + ['left'] * i)
            inputs.append(['cw'] + ['right'] * i)
            inputs.append(['ccw'] + ['right'] + ['left'] * i)
            inputs.append(['ccw'] + ['right'] + ['right'] * i)
        return inputs


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta.contracts
    python_ta.contracts.check_all_contracts()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['copy', 'game'],  # the names (strs) of imported modules
        'allowed-io': [],  # the names (strs) of functions that call print/open/input
        'max-line-length': 100,
        'disable': ['E1136', 'R0902', 'R0913'],
    })

