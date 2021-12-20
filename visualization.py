"""
File for visualizing two games side by side
"""
import time
from typing import List
import sys

import pygame
import pygame.locals
import game

SCREEN_SIZE = (700, 700)

COLOURS = {
    # dict of colours used for the pieces and background
    '': (0, 0, 0),
    'bg': (0, 0, 0),
    'g': (150, 150, 150),
    'i': (37, 219, 219),
    'j': (24, 24, 222),
    'l': (250, 158, 20),
    'o': (250, 250, 30),
    's': (55, 250, 22),
    't': (140, 30, 250),
    'z': (255, 15, 55),
}


class TetrisBoard:
    """A Tetris GameBoard
    Instance Attributes:
      - player: used to keep track of the board being used
                by the 2 players; player 1 is on the left,
                player 2 is on the right
      - loser: used to keep track of whether this player has lost,
                is False when player has won or game is in progress

    Representation Invariants:
      - self.player == 1 or self.player == 2
    """
    player: int
    loser: bool

    def __init__(self, screen: pygame.Surface, player: int, game_state: game.TetrominoGame) -> None:
        """Initialize a new Tetris Board
        """
        self.player = player
        self.loser = False
        self.draw_grid(screen)
        self.draw_blocks(screen, game_state.board)
        self.draw_queue_hold(screen, game_state.held, 'hold')
        self.draw_queue_hold(screen, game_state.get_piece(1), 'queue')

    def draw_grid(self, screen: pygame.Surface) -> None:
        """Draw 10x20 grid on the given surface. This grid represents the Tetris
         board where tetrominos will be placed.
        If the current player is 1, the grid is drawn on the left.
        Elsewise, the grid is drawn on the right.

        Preconditions:
          - self.player == 1 or self.player == 2
        """
        # colours of the grid lines
        grid_colour = (100, 100, 100)

        # draws grid on left side
        if self.player == 1:
            pygame.draw.line(screen, grid_colour, (10, 125), (10, 625))

            for col in range(1, 11):
                x = col * 25
                pygame.draw.line(screen, grid_colour, (x + 9, 125), (x + 9, 625))

            for row in range(1, 22):
                y = row * 25
                pygame.draw.line(screen, grid_colour, (10, y + 100), (259, y + 100))

        # draws grid on right side
        elif self.player == 2:
            pygame.draw.line(screen, grid_colour, (439, 125), (439, 625))

            for col in range(1, 11):
                x = col * 25
                pygame.draw.line(screen, grid_colour, (x + 439, 125), (x + 439, 625))

            for row in range(1, 22):
                y = row * 25
                pygame.draw.line(screen, grid_colour, (440, y + 100), (689, y + 100))

    def draw_blocks(self, screen: pygame.Surface, positions: List[List[str]]) -> None:
        """Fill in the proper squares on the board based on the current state of the board.
        Positions is a list of lists representing a flipped version of the
        positioning of all tetrominos on the board.
        For example:
        positions = [['i','i','i','i','','','','','',''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', ''],
              ['', '', '', '', '', '', '', '', '', '']]
          will have an i piece on the bottom left corner of the board.

        Preconditions:
          - self.player == 1 or self.player == 2
          - all([cell in ('i', 'j', 'l', 's', 'z', 'o', 't', 'g', '')
          for cell in row] for row in positions)
        """

        # draw the board for player 1
        if self.player == 1:
            pygame.draw.rect(screen, (0, 0, 0), (10, 100, 260, 550), width=0)
            for row in range(0, 20):
                for column in range(10):
                    # if piece exists, fill in the square according to the colours of the piece
                    if positions[row][column] != '':
                        piece = positions[row][column]
                        square_colours = COLOURS[piece]
                        pygame.draw.rect(
                            screen,
                            square_colours,
                            ((column * 25) + 10,
                             ((19 - row) * 25) + 125,
                             25, 25),
                            width=0)

        # draw the board for player 2
        elif self.player == 2:
            pygame.draw.rect(screen, (0, 0, 0), (439, 100, 260, 550), width=0)
            for row in range(0, 20):
                for column in range(10):
                    # if piece exists, fill in the square according to the colours of the piece
                    if positions[row][column] != '':
                        piece = positions[row][column]
                        square_colours = COLOURS[piece]
                        pygame.draw.rect(
                            screen,
                            square_colours,
                            ((column * 25) + 439,
                             ((19 - row) * 25) + 125,
                             25, 25),
                            width=0)
        # draw grid on top to show definition between blocks
        self.draw_grid(screen)

    def draw_text(self, screen: pygame.Surface, position: List[int], text: str, size: int) -> None:
        """Draw text on the screen based on the input text.

        Preconditions:
            - all(coord >= 0 for coord in position)
            - size > 0
        """
        font = pygame.font.SysFont('inconsolata', size)
        text_surface = font.render(text, True, (255, 255, 255))
        width, height = text_surface.get_size()
        screen.blit(text_surface, pygame.Rect(position[0], position[1] - 25, position[0] + width,
                                              position[1] + height))

    def draw_queue_hold(self, screen: pygame.Surface, piece: str, draw_type: str) -> None:
        """Draw the appropriate tetromino for the queue or hold given the piece type and position.
        The position will change depending on the draw_type.
        The function does not update the queue/hold if there are no tetrominos
        in the hold or queue.

        Preconditions:
          - draw_type == 'queue' or draw_type == 'hold'
          - piece in COLOURS
        """
        # update positioning based on player and draw_type
        if self.player == 1:
            if draw_type == 'queue':
                position = [280, 150]
                pygame.draw.rect(screen, (0, 0, 0),
                                 (position[0] - 10, position[1] - 50, 100, 100),
                                 width=0)
                self.draw_text(screen, [position[0] - 10, position[1]], 'NEXT PIECE', 15)
            else:
                position = [280, 300]
                pygame.draw.rect(screen, (0, 0, 0),
                                 (position[0] - 10, position[1] - 50, 100, 100),
                                 width=0)
                self.draw_text(screen, [position[0] + 5, position[1]], 'HOLD', 15)

        else:
            if draw_type == 'queue':
                position = [380, 150]
                pygame.draw.rect(screen, (0, 0, 0),
                                 (position[0] - 10, position[1] - 50, 60, 100),
                                 width=0)
                self.draw_text(screen, [position[0] - 10, position[1]], 'NEXT PIECE', 15)
            else:
                position = [380, 300]
                pygame.draw.rect(screen, (0, 0, 0),
                                 (position[0] - 10, position[1] - 50, 50, 100),
                                 width=0)
                self.draw_text(screen, [position[0] + 5, position[1]], 'HOLD', 15)

        square_colours = COLOURS[piece]

        if piece == 'i':
            pygame.draw.rect(screen, square_colours,
                             (position[0], position[1], 40, 10),
                             width=0)

        elif piece == 'j':
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 5, position[1], 30, 10),
                             width=0)

            pygame.draw.rect(screen, square_colours,
                             (position[0] + 5, position[1] - 10, 10, 10),
                             width=0)

        elif piece == 'l':
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 5, position[1], 30, 10),
                             width=0)
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 25, position[1] - 10, 10, 10),
                             width=0)

        elif piece == 'o':
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 10, position[1], 20, 20),
                             width=0)

        elif piece == 's':
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 15, position[1], 20, 10),
                             width=0)

            pygame.draw.rect(screen, square_colours,
                             (position[0] + 5, position[1] + 10, 20, 10),
                             width=0)

        elif piece == 't':
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 5, position[1], 30, 10),
                             width=0)

            pygame.draw.rect(screen, square_colours,
                             (position[0] + 15, position[1] - 10, 10, 10),
                             width=0)

        elif piece == 'z':
            pygame.draw.rect(screen, square_colours,
                             (position[0] + 5, position[1], 20, 10),
                             width=0)

            pygame.draw.rect(screen, square_colours,
                             (position[0] + 15, position[1] + 10, 20, 10),
                             width=0)
        else:
            # if the hold/queue is empty
            return

    def update_winner(self, screen: pygame.Surface, game_over: str) -> None:
        """Display whether the player has won or lost.

        Preconditions:
        - game_over == 'win' or game_over == 'lose'
        """
        # Get position of text based on curr player
        if self.player == 1:
            if game_over == 'win':
                position = [30, 350]
            else:
                position = [16, 350]
        else:
            if game_over == 'win':
                position = [458, 350]
            else:
                position = [445, 350]

        # Update screen to alert player if they won or lost
        if game_over == 'lose':
            self.draw_text(screen, position, 'YOU LOSE !! :(', 50)
        elif game_over == 'win':
            self.draw_text(screen, position, 'YOU WIN !! :)', 50)


class Visualizer:
    """
    A class responsible for creating a Pygame window to display two Tetris Boards
    Private Instance Attributes:
    - _screen: the pygame display surface
    - _p1: a TetrisBoard displaying the state of player 1
    - _p2: a TetrisBoard displaying the state of player 2
    """
    _screen: pygame.Surface
    _p1: TetrisBoard
    _p2: TetrisBoard

    def __init__(self, screen_size: tuple[int, int], player1: game.TetrominoGame,
                 player2: game.TetrominoGame) -> None:
        """Initialize a new visualizer that has a screen with the given size,
        and displays player1's state on the left, and player2's state on the right.

          Preconditions:
              - screen_size[0] > 0 and screen_size[1] > 0
          """
        self._screen = self.initialize_screen(screen_size)
        self._p1 = TetrisBoard(self._screen, 1, player1)
        self._p2 = TetrisBoard(self._screen, 2, player2)
        pygame.display.update()

    def initialize_screen(self, screen_size: tuple[int, int]) -> pygame.Surface:
        """Initialize a Pygame screen.
        """
        # ensure python module is initialized
        if not pygame.get_init():
            pygame.init()
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode(screen_size)
        screen.fill(COLOURS['bg'])
        pygame.display.flip()
        pygame.display.set_caption('Tetris!')

        pygame.event.clear()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

        return screen

    def update_board(self, player: int, game_state: game.TetrominoGame) -> None:
        """The game board is updated based on new moves.
        If the game is over, display the winner.

        Preconditions:
        - player == 1 or player == 2
        """
        self.check_terminate()
        if game_state.game_over and player == 1:
            # game ends for player1, and they therefore lose
            self._p1.loser = True
            self._p2.update_winner(self._screen, 'win')
            self._p1.update_winner(self._screen, 'lose')
            return
        elif game_state.game_over and player == 2:
            # game ends for player2, and they therefore lose
            self._p2.loser = True
            self._p1.update_winner(self._screen, 'win')
            self._p2.update_winner(self._screen, 'lose')
            return

        elif player == 1 and not game_state.game_over and not self._p2.loser:
            # the game is not over, so update the board, hold, and queue
            self._p1.draw_blocks(self._screen, game_state.board)
            self._p1.draw_queue_hold(self._screen, game_state.held, 'hold')
            self._p1.draw_queue_hold(self._screen, game_state.get_piece(1), 'queue')
        elif player == 2 and not game_state.game_over and not self._p1.loser:
            # the game is not over, so update the board, hold, and queue
            self._p2.draw_blocks(self._screen, game_state.board)
            self._p2.draw_queue_hold(self._screen, game_state.held, 'hold')
            self._p2.draw_queue_hold(self._screen, game_state.get_piece(1), 'queue')
        pygame.display.update()

    def check_terminate(self) -> None:
        """Check if the user has triggered the quit event or pressed esc
        to close the Pygame display and end the running program"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN \
                    and event.key == pygame.K_ESCAPE:
                self.terminate()
                sys.exit()

    def terminate(self) -> None:
        """Terminate the Pygame Window"""
        pygame.display.quit()

    def wake(self) -> None:
        """Make sure the OS thinks the game hasn't crashed"""
        pygame.event.get()


def initialize_screen(screen_size: tuple[int, int], allowed: list) -> pygame.Surface:
    """Initialize pygame and the display window.
    This is a testing function to allow for testing of Board without
    a Visualizer!
    """
    pygame.display.init()
    pygame.display.set_caption('Tetris!')
    pygame.font.init()
    screen = pygame.display.set_mode(screen_size)
    screen.fill((0, 0, 0))
    pygame.display.flip()

    pygame.event.clear()
    pygame.event.set_blocked(None)
    pygame.event.set_allowed([pygame.QUIT] + allowed)

    return screen


def test() -> None:
    """A testing function used to test the Visualizer and Board together

    Preconditions:
      - all([cell in ('i', 'j', 'l', 's', 'z', 'o', 't', 'g', '')
          for cell in row] for row in positions)
      - screen_size[0] > 0 and screen_size[1] > 0
    """
    queue1 = ['t', 'z']
    player1 = game.TetrominoGame(queue1)
    queue2 = ['o', 's']
    player2 = game.TetrominoGame(queue2)
    screen = Visualizer((700, 700), player1, player2)
    time.sleep(2)
    player1.change_board([17, 5], 0)
    player2.change_board([16, 2], 0)
    screen.update_board(1, player1)
    screen.update_board(2, player2)

    pygame.display.flip()
    pygame.event.wait()
    pygame.display.quit()


if __name__ == '__main__':
    # import doctest
    # doctest.testmod()

    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()

    import python_ta
    python_ta.check_all(config={
        'max-line-length': 100,
        'disable': ['E1136', 'R0912', 'R0201', 'E1101'],
        'extra-imports': ['pygame', 'typing', 'time',
                          'pygame.locals', 'sys', 'game'],
        'max-nested-blocks': 4
    })
