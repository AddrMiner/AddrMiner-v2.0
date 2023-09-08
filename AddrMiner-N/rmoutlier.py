import numpy as np
import networkx as nx
from Definitions import Node
from tools import numConversion,numConversion_rev

# the max free dimensions you can tolerate 
threshold = 12


def seed_distance(a, b):
    return len(np.argwhere(a != b))

def density(arrs):
    if len(arrs) == 1:
        return 0

    Tarrs = arrs.T

    xi = np.count_nonzero([
        np.count_nonzero(np.bincount(Tarrs[i], minlength=16)) - 1
        for i in range(32)
    ])
    if xi == 0:
        return 0

    return len(arrs) / xi


def seeds_to_arrs(seeds:list):
    result = np.array([numConversion(seeds[0])])
    for seed in seeds[1:]:
        result = np.concatenate((np.array([numConversion(seed)]), result), axis=0)
    return result

def arrs_to_seeds(arrs):
    result = []
    for i in range(arrs.shape[0]):
        result.append(numConversion_rev(arrs[i, :]))
    return result

def arrs_to_seeds_1(arrs):
    return numConversion_rev(arrs)


def OutlierDetect(node:Node, xi:int):
    # ndarray(此区域的种子数量，32)
    if node.size <= xi:return [node], []
    arrs = seeds_to_arrs(node.w)
    if len(arrs) <= 1:
        return [], [arrs]

    # init the egde weight
    dis = []
    for i in range(len(arrs)):
        for j in range(i + 1, len(arrs)):
            w = seed_distance(arrs[i], arrs[j])
            if w > threshold:
                continue
            dis.append((i, j, w))

    dis = sorted(dis, key=lambda x: x[2])

    # Kruskal alg build the mst

    G = nx.Graph()
    G.add_nodes_from(range(len(arrs)))
    for i, j, w in dis:
        # 返回 i j 所有可达节点
        idescendants = nx.algorithms.descendants(G, i)
        jdescendants = nx.algorithms.descendants(G, j)
        idescendants.add(i)
        jdescendants.add(j)
        if (i in jdescendants):
            # 同一个联通分量 不加
            continue
        if density(arrs[list(idescendants | jdescendants)]) > density(
                arrs[list(idescendants)]) and density(
                    arrs[list(idescendants | jdescendants)]) > density(
                        arrs[list(jdescendants)]):
            # 计算两个联通分量的密度
            G.add_edge(i, j, len=w)
    patterns = []
    outliers = []
    for l in list(nx.connected_components(G)):
        l = list(l)
        if len(l) > 1:
            patterns.append(arrs[l])
        else:
            outliers.append(arrs[l[0]])

    # showPatternAndOutliers(patterns, outliers)
    pattern_nodes = []
    for pattern in patterns:
        new_seeds = arrs_to_seeds(pattern)
        node = Node(new_seeds)
        pattern_nodes.append(node)
    outliers_lis = []
    for outlier in outliers:
        outliers_lis.append(arrs_to_seeds_1(outlier))
    return pattern_nodes, outliers_lis
    # pattern_nodes:list(处理后的区域数量)，每个元素是一个node
    # outliers:list(游离点数量)
