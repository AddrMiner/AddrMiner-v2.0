import pickle
from Definitions import *
from queue import Queue
from tools import listReverse,entro

def dataloader(input_path):
    seeds = []
    with open(input_path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            seeds.append(list(line))
    return seeds

    
def Region_cluster(seeds, delta):
    root = Node(seeds)
    Leaves = set()
    DQ = Queue()
    DQ.put(root)

    while not DQ.empty():
        cur = DQ.get()
        if cur.size <= delta:
            Leaves.add(cur)
            continue
        children = Split(cur)
        for child in children:
            DQ.put(child)
    
    return list(Leaves)
        
def Split(node:Node):
    S = node.w
    RS = listReverse(S)
    children = set()

    free_dim = dict()
    for dim in range(32):
        entropy = entro(RS[dim])  # 修改过
        if entropy == 0: continue
        else:free_dim[dim] = entropy
        # entropy = Statistics.entropy(RS[dim])
        # if entro == 0: continue
        # else:free_dim[dim] = entro

    if len(free_dim)==0 : return []

    sorted_freedim = sorted(free_dim.items(), key = lambda x:x[1])
    min_entropy = sorted_freedim[0][1]
    # 最小熵分裂，最外面的for循环是对熵值一样的每一位都进行划分
    for i in range(len(sorted_freedim)):
        if sorted_freedim[i][1] > min_entropy:break
        clusters = dict()
        dim = sorted_freedim[i][0]
        for addr in S:
            ch = addr[dim]
            if ch not in clusters: clusters[ch] = [addr]
            else:
                clusters[ch].append(addr)
        for key in clusters:
            children.add(Node(clusters[key]))

    return list(children)

def write_pattern(Leafs):
    with open("Data/patterns.txt", 'w') as f:
        for i in range(len(Leafs)):
            f.write("No.{} address pattern|size:{}\n".format(i,Leafs[i].size))
            f.write(Leafs[i].pattern+"\n")
            f.write("-"*32+"\n")
            for addr in Leafs[i].w:
                f.write("\""+addr+"\","+"\n")
            f.write("\n")

    with open("Data/nodes",'wb') as f:
        pickle.dump(Leafs,f)

