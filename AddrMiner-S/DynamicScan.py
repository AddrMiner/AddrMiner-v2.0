#!/usr/bin/python3.6
# encoding:utf-8
import logging
from Definitions import Intersection
from AddrsToSeq import InputAddrs, SeqToAddrs
from DHC import SpaceTreeGen, OutputSpaceTree
from ScanPre import ScanPre
from ActiveScan import Scan
from copy import deepcopy
import argparse
import math
import time

"""
sudo python3 DynamicScan.py --input=/home/liguo/ipv6_project/6density/data1.csv --output=/home/liguo/ipv6_project/6density --budget=500  --IPv6=2001:da8:ff:212::10:3 --delta=16 --beta=16
"""

def DynamicScan(root, args):
    """
    动态扫描空间树

    Args：
        root：空间树的根结点
        V：种子地址向量序列
        budget：扫描开销上限（最多扫描的地址数量）
        batch: 每轮扫描的次数
        alpha: 迭代参数
        source_ip：主机源IPv6地址
        output_dir：输出文件目录

    Return：
        R：经扫描发现的活跃地址集合（每个成员为真实的IPv6地址字符串）【序列？】
        P：检测到的别名前缀集合
        budget：剩余扫描次数
    """
    # OutputSpaceTree(root,V)
    # R = set()
    budget = args.budget
    batch = args.batch_size
    output_dir = args.output

    R = set()
    T = set()
    now_budget = deepcopy(budget)
    active_file = output_dir + '/6density.result'+str(budget)
    target_file = output_dir + '/6density.target'+str(budget)
    xi = [] # 待扫描结点队列ξ
    all_Reward = []
    InitializeNodeQueue(root, xi, all_Reward)
    all_Reward = sorted(all_Reward,reverse=True)
    xi = sorted(xi, key=lambda node: node.R, reverse=True)
    epoch = 0
    while 1:
        logging.info("Epoch: {}".format(epoch))
        xi, now_budget, R, T= Scan_Feedback(xi, budget, now_budget, R, T,  all_Reward, args)
        all_Reward = ReplaceDescendants(xi, args)
        xi = sorted(xi, key=lambda node: node.R, reverse=True)
        all_Reward = sorted(all_Reward, reverse=True)
        epoch+=1
        # 采用截取式 最终采样次数位于 [budget-batch, budget]
        if now_budget < batch:
            break


    print("begin to store the ip address in {} and {}".format(active_file, target_file))
    with open(active_file, 'w', encoding='utf-8') as f:
        for addr in R:
            f.write(addr + '\n')
    with open(target_file, 'w', encoding='utf-8') as f:
        for target in T:
            f.write(target + '\n')
    hit_rate = float(len(R))/(budget - now_budget)
    return R, budget-now_budget, len(R), hit_rate


def InitializeNodeQueue(root, xi, all_Reward):
    """
    层次遍历空间树，将结点队列ξ初始化为空间树的叶子结点

    Args：
        root:空间树的根结点
        xi：结点队列ξ
    """
    # pdb.set_trace()
    q = []
    q.append(root)
    while q != []:
        node = q.pop(0)
        if node.childs != []:  # 如果为空则为叶子节点
            q += node.childs
        else:
            xi.append(node)  # 存储叶子节点
            all_Reward.append(node.R)

def Scan_Feedback(xi, budget,now_budget, R, T, all_Reward, args):
    """
    对队列xi中的所有结点进行一次扫描，
    并根据扫描得到的活跃地址密度对队列重新排序

    Args：
        xi：结点队列ξ
        budget：总扫描次数
        now_budget：剩余扫描次数
        batch_size：本次扫描的次数
        R：经扫描发现的活跃地址集合
        T
        V:种子地址向量集合
        source_ip
        output_dir
        target_file

    Return:
        xi:重新排序后的结点队列ξ
        budget:经过一次迭代扫描之后剩余的扫描次数
        R：更新后的活跃地址集合
        T：预测地址集合
    """

    # pdb.set_trace()
    batch_size = args.batch_size
    source_ip = args.IPv6
    output_dir = args.output
    alpha = args.alpha
    num_node = args.num_node
    TS_addr_union = list()
    SS_addr_union = list()
    sum_Reward = 0.0
    for i in range(min(len(xi), args.num_node)):  # 防止越界
        sum_Reward += all_Reward[i]
        #sum_Reward += math.exp(all_Reward[i])
    for i in range(min(len(xi), args.num_node)):
        # if i % 100 == 0:
        #     print(i)
        node = xi[i]
        #logging.info("Node ID {}".format(node.node_id))
        #print("Node ID {}".format(node.node_id))
        #logging.info("Reward: {}".format(node.R))
        #print("Reward:", node.R)
        #sample_result = SeqToAddrs(node, int((math.exp(all_Reward[i])/sum_Reward)*batch_size),args)
        sample_result = SeqToAddrs(node, int((all_Reward[i] / sum_Reward) * batch_size), args)
        TS_addr_union += sample_result
        SS_addr_union += list(node.SS)  # 扫描过的IPv6地址字符串集合
        node.SS.update(set(sample_result))
    C = set(TS_addr_union).difference(set(SS_addr_union)) #本次需要扫描的地址集合
    now_budget -= len(C)
    T.update(C)
    # with open(target_file, 'a', encoding='utf-8') as f:
    #     for target in C:
    #         f.write(target + '\n')
    active_addrs = set(Scan(C, source_ip, output_dir, 0))   #扫描并得到活跃的地址集合

    R.update(active_addrs)
    logging.info('[+]Hit rate:{}   Remaining scan times:{}\n'
       .format(float(len(R)/ (budget-now_budget)), now_budget))
    print('[+]Hit rate:{}   Remaining scan times:{}\n'
       .format(float(len(R)/ (budget-now_budget)), now_budget))

    for i in range(min(len(xi), args.num_node)):  # 更新节点的属性
        # if(i % 100 == 0):
        #     print(i)
        node = xi[i]
        new_active_addrs = active_addrs.intersection(node.SS)   # 寻找全部节点中与node.ss相似 的节点集合
        node.R = (1-alpha)*node.R + alpha*float(len(new_active_addrs))/len(node.DR)  # 密度属性  更改成reward值

    xi = sorted(xi, key=lambda node: node.R, reverse=True)
    return xi, now_budget, R, T


def TakeOutFrontSegment(xi, m):
    """
    提取结点队列xi中的前m个结点，作为下次扫描的目标结点队列

    Args：
        xi:待分割的队列
        m：新目标队列的结点数

    Return：
        xi_h：新的目标队列
    """

    # xi_h = deepcopy(xi[:m])
    # pdb.set_trace()

    if m <= len(xi):
        xi_h = xi[:m]
        del xi[:m]
    else:
        xi_h = xi[:]
        del xi[:]

    return xi_h


def ReplaceDescendants(xi, args):
    """
    经过一次扫描后，若某结点的密度过大，在xi和xi_h队列中，
    需要将该结点及其所有的兄弟结点删除，并插入它们的父结点【证  明见Theorom3】

    Args：
        xi_h：下次将会被扫描的结点队列
        delta: 基数
    """

    # pdb.set_trace()

    for node in xi:
        if node.parent == None:
            break   #注释！！！！！
        if node.parent.DS.stack == node.DS.stack:
            # 将父节点加入集合中
            # 将父节点的子节点的值加入其中
            # 将子节点从中去除
            parent = node.parent
            sum_child_R = 0.0
            sum_child_DR = set()
            max_dim = 0
            for node_i in parent.childs:
                parent.SS.update(node_i.SS)
                sum_child_R += node_i.R*len(node.DR)  # 合并R值
                sum_child_DR.update(set(node_i.DR))
                try:
                    xi.remove(node_i)  #防止其他节点未加入
                except:
                    pass
                max_dim = max(max_dim, node_i.searched_dim)
            parent.searched_dim = max_dim
            parent.DR = list(set(parent.DR) | sum_child_DR)  # 搜索空间 DR也要合并
            #parent.R = math.pow(delta, len(parent.DR) - len(sum_child_DR)) * sum_child_R
            parent.R = sum_child_R/len(parent.DR)  # 假定 父节点与子节点 空间大小与reward
            parent.ExpandTS(list(sum_child_DR))
            parent.region_size = pow(args.delta, parent.searched_dim) * len(parent.TS)
            xi.append(parent)

    all_Reward = []
    for new_node in xi:
        all_Reward.append(new_node.R)
    return all_Reward

def MergeSort(xi_h, xi):
    """
    将两个有序的结点队列合并为一个

    Args：
        xi_h：队列1
        xi：队列2

    Return：
        queue：合并后的有序队列
    """

    queue = []
    i1 = 0
    i2 = 0
    while i1 < len(xi_h) or i2 < len(xi):
        if i1 >= len(xi_h):
            queue += xi[i2:]
            break
        elif i2 >= len(xi):
            queue += xi_h[i1:]
            break
        elif xi_h[i1].AAD >= xi[i2].AAD:
            queue.append(xi_h[i1])
            i1 += 1
        else:
            queue.append(xi[i2])
            i2 += 1

    return queue


def LimitBudget(budget, C):
    """
    将C中超出预算部分的地址删除

    Args:
        budget: 超过预算的地址数的相反数
        C：下次将要扫描的目标地址集合

    Return:
        C：经过处理后的目标地址集合
    """

    C = list(C)
    del C[:-budget]
    return set(C)


def Start():
    parse=argparse.ArgumentParser()
    parse.add_argument('--input', type=str, default="testData.txt",help='input IPv6 addresses')
    parse.add_argument('--output',type=str, default="/home/szx/code/result",help='output directory name')
    parse.add_argument('--budget',type=int, default=10000000, help='the upperbound of scan times')
    parse.add_argument('--IPv6',type=str, default="2001:da8:ff:212::7:8", help='local IPv6 address')
    parse.add_argument('--delta', type=int, default=16, help='the base of address')
    parse.add_argument('--beta',type=int, default=16, help='the max of node ')
    parse.add_argument('--alpha',type=float, default=0.1,help='the parameter of RL ')
    parse.add_argument('--batch_size', type=int, default=100000, help='the parameter for each epoch')
    parse.add_argument('--num_node', type=int, default=500, help='the parameter for each epoch')
    args=parse.parse_args()
    # args.input = '/home/sgl/6density_no_APD/files/source_copy.hex'
    # args.output = '/home/sgl/6density_no_APD/files2'
    # args.budget = 50000
    # args.IPv6 = '2001:da8:ff:212::20:5'

    # IPS=InputAddrs(input="data1.csv")
    # root=SpaceTreeGen(IPS,16,16)
    # OutputSpaceTree(root)
    logging.basicConfig(filename='my_{},alpha={},num_node={},batch={}.log'.format(args.budget, args.alpha, args.num_node, args.batch_size), level=logging.INFO)
    print("ipv6 addres to sec begining")
    print(args.input)
    V = InputAddrs(input=args.input, beta=args.delta)
    print("ipv6 addres to sec over")
    print("SpaceTreeGen beginning")
    root = SpaceTreeGen(V, delta=args.delta, beta=args.beta)
    print("SpaceTreeGen over")
    ScanPre(root)
    # OutputSpaceTree(root,V)
    print('Space tree generated with {} seeds!'.format(len(V)))    
    R, target_len, result_len, hit_rate = DynamicScan(root, args)
    print('Over!')
    # hit_rate = float(len(R))/(init_budget - budget)
    # return init_budget - budget, len(R), hit_rate
    return target_len, result_len, hit_rate


if __name__ == '__main__':
    target, result, hit_rate = Start()
    print("target {}".format(target))
    print("result {}".format(result))
    print("hit_rate {}".format(hit_rate))

    
