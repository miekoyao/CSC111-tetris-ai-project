"""
CSC111 Final Project

This is the main file and will generate queues and run AI vs AI games
"""
from random import shuffle, random, choice
from typing import List, Tuple
from time import sleep
import csv
from visualization import Visualizer
from game import TetrominoGame
from eval import TetrominoAI
from graph import format_csv, generate_graph

SIZE = 20  # number of members in the population


def seven_bag() -> List[str]:
    """Return a shuffled 7-bag of pieces"""
    pieces = ['s', 'z', 't', 'o', 'i', 'j', 'l']
    shuffle(pieces)
    return pieces


def generate_queue(length: int) -> List[str]:
    """Generate the queue using a seven bag randomizer

    Preconditions:
    - length > 0
    """
    queue = []
    while len(queue) < length:
        queue.extend(seven_bag())
    return queue


def test(weight1: List[float], weight2: List[float]) -> Tuple[int, float, float]:
    """Display a battle between AIs using two weights

    Preconditions:
    - len(weight1) == 12
    - len(weight2) == 12
    - all([weight <= 2.1 for weight in weight1])
    - all([weight <= 2.1 for weight in weight2])
    """
    # generate a ~10000 length 7-bag queue and initialize the games, the AIs and the visualizer.
    queue = generate_queue(10000)
    g1 = TetrominoGame(queue)
    g2 = TetrominoGame(queue)
    a1 = TetrominoAI(g1, 2, 2, weight1)
    a2 = TetrominoAI(g2, 2, 2, weight2)
    v = Visualizer((700, 700), g1, g2)
    sleep(1)
    # play the game until one loses
    while g1.game_over is not True and g2.game_over is not True:
        v.wake()  # make sure the visualization does not freeze
        a1.generate_tree()
        a2.generate_tree()
        a1.make_move()
        a2.make_move()
        g1.pending_garbage.extend(g2.sent_garbage)
        g2.pending_garbage.extend(g1.sent_garbage)
        g1.sent_garbage.clear()
        g2.sent_garbage.clear()
        v.update_board(1, g1)
        v.update_board(2, g2)
        # add a delay
        # sleep(0.3)
    v.update_board(1, g1)
    v.update_board(2, g2)
    app1 = g1.get_app()
    app2 = g2.get_app()
    sleep(1)
    v.terminate()

    # return 1 if the winner used weight1, 2 if the winner used weight2
    # also return the APP of both games
    if g1.game_over is True:
        return (2, app1, app2)
    else:
        return (1, app1, app2)


def initiate(size: int = SIZE) -> List[List[float]]:
    """Make an initial population using random weights

    Preconditions:
    - size >= 2"""
    p = []
    while len(p) < size:
        p.append([random() for _ in range(0, 12)])
    return p


def compare(population: List[List[float]]) -> List[List[float]]:
    """Determine the best members of the population using win/loss count.
    Ties are broken with attack per piece.
    """
    # match each member of the population which every other member
    pairings = []
    scores = [0 for _ in range(0, len(population))]
    app = [[] for _ in range(0, len(population))]
    for i in range(0, len(population)):
        for j in range(i + 1, len(population)):
            pairings.append([i, j])

    # test the pair against each other and determine the winner in a 1v1
    for pair in pairings:
        # print(pair)
        results = test(population[pair[0]], population[pair[1]])
        if results[0] == 1:
            scores[pair[0]] += 1
        else:
            scores[pair[1]] += 1
        app[pair[0]].append(results[1])
        app[pair[1]].append(results[2])

    # average the APP for each player
    for i in range(0, len(app)):
        app[i] = sum(app[i]) / len(app[i])
    # keep only the best half of the population
    best = []
    while len(best) < len(population) / 2:
        max_wins = max(scores)
        # break ties with APP
        tied = [h for h in range(0, len(population)) if scores[h] == max_wins]
        tied_app = [app[k] for k in tied]
        while len(best) < len(population) / 2 and tied != []:
            tied_index = tied_app.index(max(tied_app))
            best.append(population[tied[tied_index]])
            scores[tied[tied_index]] = -1
            tied.pop(tied_index)
            tied_app.pop(tied_index)
    return best


def refill(parents: List[List[float]], size: int = SIZE) -> List[List[float]]:
    """Refill the population to size by making
    children with the original population as parents

    Preconditions:
    - size >= 2"""
    children = []
    while len(parents) + len(children) < size:
        children.append(cross(choice(parents), choice(parents)))
    children.extend(parents)
    return children


def cross(p1: List[float], p2: List[float]) -> List[float]:
    """Make a cross between two parents with a chance of mutation"""
    child = []
    for i in range(0, len(p1)):
        child.append(choice([p1[i], p2[i]]))
        if random() < 0.1:
            child[i] += (child[i] + 0.2) * (0.15 * (random() - random()))
    return child


def read_csv() -> List[List[float]]:
    """Read all members of csv."""
    reader = csv.reader(open('weights.csv', 'r', newline=''), quoting=csv.QUOTE_NONNUMERIC)
    weights = []
    for row in reader:
        weights.append(row)
    return weights


def write_csv(weights: List[List[float]]) -> None:
    """Write a population to weights.csv"""
    original = read_csv()
    writer = csv.writer(open('weights.csv', 'w', newline=''))
    writer.writerows(original + weights)


def run(size: int = SIZE) -> None:
    """Create an initial population if none available and test members of the population against
    one another to try and select for traits that provide the best chance to win in a 1v1 game.

    Preconditions:
    - size >= 2"""
    # read weights.csv for previous weights
    prev_weights = read_csv()
    # make a new population if not enough previous members
    if len(prev_weights) < size:
        population = initiate()
    # otherwise, use the most recent weights
    else:
        population = [prev_weights[len(prev_weights) - i - 1]
                      for i in range(0, size)]
    # compare the weights in the population
    best = compare(population)
    population = refill(best)

    # write the next generation to the weights.csv
    write_csv(population)


def run_fresh() -> None:
    """Initialize a new population and compare the members"""
    population = initiate()
    compare(population)


def runner(num_times: int) -> None:
    """Run the comparisons num_times times"""
    for _ in range(0, num_times):
        run()


def draw_graph() -> None:
    """Generate a graph to show the weight values stored in weights.csv"""
    data = format_csv()
    generate_graph(data)
