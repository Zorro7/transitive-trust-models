import networkx as nx
import numpy as np

import utils

def single_eigen_ht(graph, restart_dist, j, alpha=0.15):
    N = graph.number_of_nodes()
    M = nx.to_numpy_matrix(graph)

    restart_dist = np.array(restart_dist)
    restart_dist /= restart_dist.sum()

    # Handling dangling nodes and normalize all rows
    for k in xrange(N):
        s = M[k].sum()
        # Dangling nodes become absorbinb states.
        if s == 0:
            M[k, k] = 1
        else:
            M[k] /= s

    # Set up the restart distribution
    M[j] = restart_dist

    ht_matrix = (1 - alpha) * M + alpha * np.outer(np.ones(N), restart_dist)

    eigenvalues, eigenvectors = np.linalg.eig(ht_matrix.T)
    dominant_index = eigenvalues.argsort()[-1]
    pagerank = np.array(eigenvectors[:, dominant_index]).flatten().real
    pagerank /= np.sum(pagerank)

    return 1.0 / (1 - alpha + alpha / pagerank[j])


def global_eigen_ht(graph, restart_dist, alpha=0.15):
    return np.array([single_eigen_ht(graph, restart_dist, j, alpha)
            for j in graph.nodes()])


def personalized_eigen_ht(graph, alpha=0.15):
    """
    Makes N^2 eigenvector calculations. Expected O(N^5).
    """
    N = graph.number_of_nodes()
    scores = np.zeros((N, N))

    for i in xrange(N):
        restart = np.zeros(N)
        restart[i] = 1
        for j in xrange(N):
            scores[i, j] = single_eigen_ht(graph, restart, j, alpha)

    return scores


def single_LA_ht(graph, j, alpha=0.15):
    N = graph.number_of_nodes()
    M = nx.to_numpy_matrix(graph)
    for i in xrange(N):  # Normalize
        M[i] /= M[i].sum()
    M[j] = 0  # Remove outedges of j
    A = np.eye(N) - (1 - alpha) * M
    b = np.repeat(1 - alpha, N)
    return -np.linalg.solve(A, b)


def personalized_LA_ht(graph, alpha=0.15):
    """ Computes personalized hitting time using a linear equation method.

    This is expected O(N^4).

    This is based on the formula

        (I - (1 - alpha) * M(j)) * h(j) = (1 - alpha) * 1

    which allows us to solve for the h_{ij} for one particular j by solving a
    system of linear equations with N variables and N equations. We repeat this
    N times to obtain all N^2 personalized hitting times.

    Returns:
        An NxN numpy matrix containing the personalized hitting times.
    """
    N = graph.number_of_nodes()
    ht = np.zeros((N, N))
    for j in xrange(N):
        ht[:, j] = single_LA_ht(graph, j, alpha)
    return ht


def global_LA_ht(graph, weights, alpha=0.15):
    """ Global hitting time using linear algebra methods.

    Args:
        graph: The trust graph.
        weights: A list of non-negative weights, in nodelist order.
        alpha: Termination probability.
    """
    ht = personalized_LA_ht(graph, alpha)
    return np.dot(np.transpose(ht), np.array(utils.normalize(weights)))
