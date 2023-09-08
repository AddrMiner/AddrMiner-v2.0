import pickle as pkl
import pyasn
from tools import *

def convert(seed):
    seed = seed.split(":")
    for i in range(len(seed)):
        if len(seed[i]) == 4:
            continue
        if len(seed[i]) < 4 and len(seed[i]) > 0:
            zero = "0"*(4 - len(seed[i]))
            seed[i] = zero + seed[i]
        if len(seed[i]) == 0:
            zeros = "0000"*(9 - len(seed))
            seed[i] = zeros
    return "".join(seed)[:32]

def get_bgp_n():
    ansdb = pyasn.pyasn("Data/ipasn.dat")
    bgp_with_seeds = {}
    bgp_n = []
    bgp_n_with_whois = []
    # 找到有种子BGP
    with open ('Data/final_seeds.txt','r') as r:
        for seed in r.readlines():
            seed = seed[:-1]
            bgp = ansdb.lookup(seed)[1]
            if bgp not in bgp_with_seeds:bgp_with_seeds[bgp]=[]
            bgp_with_seeds[bgp].append(convert(seed))

    # 找到无种子的BGP
    with open ('Data/ipasn.dat','r') as f:
        for line in f.readlines()[6:]:
            bgp = line.split()[0]
            if bgp not in bgp_with_seeds:
                bgp_n.append(bgp)

    # 找到无种子有whois信息的BGP
    # for root, dirs, filenames in os.walk('new_whois'):
    #     for filename in filenames:
    #         try:
    #             stdbgp = stdprefix(filename)
    #         except:continue
    #         if stdbgp in bgp_n:
    #             bgp_n_with_whois.append(stdbgp)
    # print(len(bgp_n_with_whois))

    # 保存
    with open('BGP/bgp_n_with_whois','w') as f:
        for i in bgp_n:
            f.write(i)
            f.write('\n')

def get_bgp_with_patterns():
    ansdb = pyasn.pyasn("Data/ipasn.dat")
    with open('Data/nodes','rb') as r:
        nodes = pkl.load(r)
    # 生成bgp和pattern的字典
    bgp_with_patterns = {}
    for node in nodes:
        if node.pattern_freeDim<=5:
            pattern = node.pattern
            addr = list(genAddrByPattern(pattern,0,1))[0]
            bgp = ansdb.lookup(addr)[1]
            if bgp not in bgp_with_patterns:bgp_with_patterns[bgp] = []
            bgp_with_patterns[bgp].append(node)
    with open('Data/bgp_with_patterns_clean','wb') as f:
        pkl.dump(bgp_with_patterns,f)
