""" Strategic Trust Models

This file provides routines that compute various trust model under strategic
manipulation. A given number of agents are chosen to be strategic, and they
perform optimal manipulations to make themselves look better, and then the
trust model scores are applied.
"""
import random
import sys

import networkx as nx
import numpy as np

from hitting_time.mat_hitting_time import personalized_LA_ht
import trust_models as tm

def cut_outlinks(graph, agents):
    graph.remove_edges_from(graph.edges(agents))


def generate_sybils(graph, agents, num_sybils):
    sybil_counter = max(graph.nodes()) + 1
    for agent in agents:
        edges = [(agent, sybil)
                 for sybil in xrange(sybil_counter, sybil_counter + num_sybils)]
        edges += map(lambda x: x[::-1], edges)
        graph.add_edges_from(edges)
        sybil_counter += num_sybils


def add_thin_edges(graph, edge_weight=1e-5):
    edges = graph.edges()
    for i in graph.nodes_iter():
        for j in graph.nodes_iter():
            if i == j:
                continue
            if (i, j) not in edges:
                graph.add_edge(i, j, weight=edge_weight)
                # We don't bother with inv_weight because this method doesn't
                # need to be used for shortest path.


def global_pagerank(graph, num_strategic, sybil_pct):
    """ Global PageRank.

    Cut all outlinks + generate sybils.
    """
    graph = graph.copy()
    N = graph.number_of_nodes()
    strategic_agents = random.sample(graph.nodes(), num_strategic)
    num_sybils = int(graph.number_of_nodes() * sybil_pct)
    cut_outlinks(graph, strategic_agents)
    generate_sybils(graph, strategic_agents, num_sybils)
    return tm.pagerank(graph)[:N]


def person_pagerank(graph, num_strategic, sybil_pct):
    """ Personalized PageRank.

    Cut all outlinks + generate one sybil.
    """
    graph = graph.copy()
    N = graph.number_of_nodes()
    strategic_agents = random.sample(graph.nodes(), num_strategic)
    cut_outlinks(graph, strategic_agents)
    generate_sybils(graph, strategic_agents, 1)
    add_thin_edges(graph)
    return tm.personalized_pagerank(graph)[:N, :N]


def global_hitting_time(graph, num_strategic, sybil_pct):
    """ Global Hitting Time.

    Cut all outlinks + generate sybils.
    """
    graph = graph.copy()
    N = graph.number_of_nodes()
    strategic_agents = random.sample(graph.nodes(), num_strategic)
    num_sybils = int(graph.number_of_nodes() * sybil_pct)
    cut_outlinks(graph, strategic_agents)
    generate_sybils(graph, strategic_agents, num_sybils)
    return tm.hitting_pagerank(graph, 'all')[:N]


def person_hitting_time(graph, num_strategic, sybil_pct):
    """ Personalized Hitting Time.

    Cut all outlinks.
    """
    graph = graph.copy()
    strategic_agents = random.sample(graph.nodes(), num_strategic)
    cut_outlinks(graph, strategic_agents)
    add_thin_edges(graph)
    return personalized_LA_ht(graph)


def person_max_flow(graph, num_strategic, sybil_pct):
    """ Personalized Max Flow.

    Cut all outlinks.
    """
    graph = graph.copy()
    N = graph.number_of_nodes()
    strategic_agents = random.sample(graph.nodes(), num_strategic)
    saved_edges = {a: graph.edges(a, data=True) for a in strategic_agents}
    cut_outlinks(graph, strategic_agents)
    add_thin_edges(graph)

    # Need to reimplement max flow here because we only want to cut outedges
    # When we're not being evaluated.
    scores = np.zeros((N, N))
    for i in xrange(N):
        # Add back in the edges for this agent, so we can get an actual score.
        if i in strategic_agents:
            for a, b, d in saved_edges[i]:
                graph[a][b]['weight'] = d['weight']

        # Now compute the max flow scores
        for j in xrange(N):
            if i == j:
                scores[i][j] = None
            else:
                mf = nx.max_flow(graph, i, j, capacity='weight')
                scores[i][j] = None if mf == 0 else mf

        # Now remove those edges again (a bit inefficiently)
        cut_outlinks(graph, [i])
        add_thin_edges(graph)

        sys.stdout.write('.')
    sys.stdout.write("\n")

    return scores


def person_shortest_path(graph, num_strategic, sybil_pct):
    """ Personalized Shortest Path.

    No manipulations.
    """
    return tm.shortest_path(graph)