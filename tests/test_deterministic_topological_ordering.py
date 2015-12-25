import unittest
from networkx.exception import NetworkXUnfeasible
from ptero_workflow.utils import\
        deterministic_topological_ordering


class TestTopologicalOrdering(unittest.TestCase):
    def test_n_shaped_dag(self):
        nodes = (999, 1, 3, 2, 4)
        links = ((0,1), (0,2), (1,3), (1,4), (2, 4), (3, 999), (4, 999))
        ordering = deterministic_topological_ordering(nodes, links, 0)
        self.assertEqual(ordering, [0, 1, 2, 3, 4, 999])

    def test_wide_dag(self):
        nodes = [x for x in range(1000)]
        links = []
        for node in nodes[1:-1]:
            links.append((nodes[0], node))
            links.append((node, nodes[-1]))

        # test different orderings of nodes and links to ensure no funny business is going on.
        ordering = deterministic_topological_ordering(reversed(nodes), reversed(links), nodes[0])
        self.assertEqual(ordering, nodes)

        ordering = deterministic_topological_ordering(nodes, reversed(links), nodes[0])
        self.assertEqual(ordering, nodes)

        ordering = deterministic_topological_ordering(nodes, links, nodes[0])
        self.assertEqual(ordering, nodes)

        ordering = deterministic_topological_ordering(reversed(nodes), links, nodes[0])
        self.assertEqual(ordering, nodes)

    def test_cyclic(self):
        nodes = (0,1,2,3,4,999)
        links = ((0,1), (0,2), (1,3), (1,4), (2, 4), (3, 999), (4, 999), (999, 0))
        with self.assertRaises(NetworkXUnfeasible):
            deterministic_topological_ordering(nodes, links, 0)
