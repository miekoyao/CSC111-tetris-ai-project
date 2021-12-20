"""
Draw a graph of the weights saved to csv.

Used to visualize the change in weights over time.
"""
import csv
from typing import List
import plotly.graph_objects as graph


def format_csv() -> List[List[float]]:
    """Read all members of csv.
    Return a list of lists with each sublist containing all values of
    a given weight factor over time.
    """
    reader = csv.reader(open('weights.csv', 'r', newline=''), quoting=csv.QUOTE_NONNUMERIC)
    weights = [[] for _ in range(0, 12)]
    for row in reader:
        for i in range(0, 12):
            weights[i].append(row[i])
    return weights


def generate_graph(weights: List[List[float]]) -> None:
    """Generate a plotly graph from the data inputted in weights

    Preconditions:
    - len(weights) == 12
    """
    x_values = list(range(0, len(weights[0])))
    weight_names = ["Punish for rough field, excluding the well",
                    "Punish holes in the board",
                    "Punish a high board to keep board low",
                    "Punish height if above half of visible board",
                    "Punish height if above 3/4 of visible board",
                    "Reward a deep well",
                    "Reward higher attack numbers",
                    "Reward combo",
                    "Punish clearing 1 or 2 lines without t-spin",
                    "Reward clearing 3-4 lines at a time",
                    "Reward T-spins",
                    "Reward All-Clears"]
    fig = graph.Figure()
    for j in range(0, 12):
        fig.add_trace(graph.Scatter(x=x_values, y=weights[j],
                                    mode='markers',
                                    name=weight_names[j]))
    fig.update_layout(title='Weight Values for AI Score Factors Over Time',
                      xaxis_title="Trials run",
                      yaxis_title="Weight Value")
    fig.show()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta.contracts
    python_ta.contracts.check_all_contracts()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['csv', 'plotly.graph_objects'],  # the names (strs) of imported modules
        'allowed-io': ['format_csv'],  # the names (strs) of functions that call print/open/input
        'max-line-length': 100,
        'disable': []
    })
