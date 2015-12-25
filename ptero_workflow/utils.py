from networkx import DiGraph
from networkx.algorithms import is_directed_acyclic_graph
from networkx.exception import NetworkXUnfeasible
import os


def base_dir():
    return os.path.dirname(os.path.abspath(__file__))


def deterministic_topological_ordering(nodes, links, start_node):
    """
    Topological sort that is deterministic because it sorts (alphabetically)
    candidates to check
    """
    graph = DiGraph()
    graph.add_nodes_from(nodes)
    for link in links:
        graph.add_edge(*link)

    if not is_directed_acyclic_graph(graph):
        raise NetworkXUnfeasible

    task_names = sorted(graph.successors(start_node))
    task_set = set(task_names)
    graph.remove_node(start_node)

    result = [start_node]
    while task_names:
        for name in task_names:
            if graph.in_degree(name) == 0:
                result.append(name)

                # it is OK to modify task_names because we break out
                # of loop below
                task_names.remove(name)

                new_successors = [t for t in graph.successors(name)
                        if t not in task_set]
                task_names.extend(new_successors)
                task_names.sort()
                task_set.update(set(new_successors))

                graph.remove_node(name)
                break

    return result
