# from select import select
import time
import subprocess
import heapq
import os
import pickle as pkl
import pyasn
import argparse

from rangeCluster import *
from convert import convert
from tools import *
import random
from correlation import *
import shutil
import threading
from rmoutlier import *


def writeFile(target, active, targetfile, activefile,mode=False):
    """
    将每一次批量探测到的结果实时记录到文件中
    Args:
        target: 目标地址集
        active: 活跃地址集
    """
    if mode:
        with open(targetfile, 'a+') as f:
            for addr in target:
                f.write(addr+'\n')

    with open(activefile, 'a+') as f:
        for addr in active:
            f.write(addr+'\n')


def Scan(addr_set, source_ip, output_file, tid):
    """
    运用扫描工具检测addr_set地址集中的活跃地址

    Args:
        addr_set:待扫描的地址集合
        source_ip
        output_file
        tid:扫描的线程id

    Return:
        active_addrs:活跃地址集合
    """

    scan_input = output_file + '/zmap/scan_input_{}.txt'.format(tid)
    scan_output = output_file + '/zmap/scan_output_{}.txt'.format(tid)

    with open(scan_input, 'w', encoding='utf-8') as f:
        for addr in addr_set:
            f.write(addr + '\n')

    active_addrs = set()
    command = 'sudo zmap --ipv6-source-ip={} --ipv6-target-file={} -M icmp6_echoscan -p 80 -q -o {}'\
        .format(source_ip, scan_input, scan_output)
    print('[+]Scanning {} addresses...'.format(len(addr_set)))
    t_start = time.time()
    p = subprocess.Popen(command, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # ret = p.poll()
    while p.poll() == None:
        pass

    if p.poll() is 0:
        # with open(output_file, 'a', encoding='utf-8') as f:
        # time.sleep(1)
        for line in open(scan_output):
            if line != '':
                active_addrs.add(line[0:len(line) - 1])
                # f.write(line)

    print('[+]Over! Scanning duration:{} s'.format(time.time() - t_start))
    print('[+]{} active addresses detected!'
          .format(len(active_addrs)))
    return active_addrs

# 小批量探测是不可行的，耗费时间
# 先进行生成，将每个节点的cache合并为一个target，探测出总的active，再去更新hitrate

def preScan(id,new_nodes,ipv6, preScan_num, miniBudget=1, targetfile='', activefile=''):
    """
    预探测(将前缀进行替换, 按照命中率初步进行排序)
    Args:
        nodes: 模式节点列表
        ipv6: 本机IPv6地址
        miniBudget: 每个模式生成的地址个数
    Return:
        nodes_heapq: 模式节点优先级队列
        target: 已探测过的目标地址集合
        pre_target_num: 预扫描的目标地址数量
        pre_active_num : 预扫描得到的活跃地址数量
    """
    nodes_heapq = []
    target = []  # 已探测过的目标地址集合
    num = preScan_num
    # 生成地址
    print('[+]Generate addresses..')
    random.shuffle(new_nodes)
    with tqdm(total=preScan_num) as pbar:
        for node in new_nodes:
            if num>0:
                cache = node.genAddr(miniBudget, True)
                target.extend(list(cache))
                num -= 1
                pbar.update(1)
            else:break
    for node in new_nodes:
        if len(node.cache) == 0:
            node.genAddr(0, True)
    # 探测
    active = Scan(set(target), ipv6, './', id)
    # 更新hitrate
    for node in new_nodes:
        if node.margin > 0:
            cache_size = len(node.cache)
            if cache_size == 0:
                node.hitrate = 0
            else:
                tmp = active.intersection(node.cache)
                node.active_num += len(tmp)
                node.hitrate = len(tmp) / cache_size
            heapq.heappush(nodes_heapq, node)
    # 写入结果
    if active:
        writeFile(target, active, targetfile, activefile,mode=False)
    return nodes_heapq, list(target), list(active)

def preprocess(nodes: list, prefix: str):
    """
    数据清洗，删除掉替换前缀后相同模式的节点
    Args:
        nodes: 地址模式节点
        prefix: 替换的地址前缀
    Return:
        new_nodes: 替换后的地址模式节点
    """
    for node in nodes:
        node.prefixReplace(prefix)
    new_nodes = set()
    for node in nodes:
        new_nodes.add(node)
    return list(new_nodes)

def scan_feedback2(id,nodes, ipv6: str, batch_size=100000, epoch=10, targetfile='', activefile=''):
    """
    反馈式扫描
    每次选取rank靠前的节点生成地址, 直至耗尽预算, 剔除掉余量为0的节点, 计算hitrate, 重新排序
    Args:
        nodes: 地址模式节点
        ipv6: 本机IPv6地址
        batch_size: 每一轮次分配的预算大小
        epoch: 扫描轮数
    Return:
        target_num: 探测的地址总量
        active_num: 发现的活跃地址总量
    """
    active_num = 0
    target_num = 0
    for i in range(epoch):
        target = []
        select_num = 0  # 本轮有多少节点参与生成
        batch_size_copy = batch_size
        # 生成目标地址
        print('epoch={}, Generate addresses..'.format(i+1))
        print('the number of nodes:', len(nodes))
        with tqdm(total=batch_size) as pbar:
            for node in nodes:
                cache = node.genAddr(batch_size_copy, prescan=False)
                batch_size_copy -= len(cache)
                target.extend(list(cache))
                select_num += 1
                pbar.update(len(cache))
                if batch_size_copy <= 0:
                    break
        # 探测
        active = Scan(set(target), ipv6, './', id)
        active_num += len(active)
        target_num += len(target)
        # 更新hitrate
        for i in range(select_num):
            node = heapq.heappop(nodes)
            cache_size = len(node.cache)
            if cache_size > 0:
                tmp = active.intersection(node.cache)
                node.active_num += len(tmp)
                node.hitrate = node.active_num / len(node.target)
            if node.margin > 0:
                heapq.heappush(nodes, node)
        # 写入结果
        writeFile(target, active, targetfile, activefile, mode=False)
    return target_num, active_num

def main(args, id = 0, num_thread = 1):
    input_path = args.input_path
    ipv6 = args.IPv6
    budget = args.budget
    miniBudget = args.miniBudget
    epoch = args.epoch
    prescan_proportion = args.prescan_proportion
    delta = 64
    prefixs = []
    save_target = False

    if os.path.exists('result'):
        shutil.rmtree('result')
    os.mkdir('result')
    if os.path.exists('zmap'):
        shutil.rmtree('zmap')
    os.mkdir('zmap')

    activefile = 'result/active_epoch{}budget{}_id{}.txt'.format(epoch, budget, id)
    targetfile = 'result/target_epoch{}budget{}_id{}.txt'.format(epoch, budget, id)
    logfile = 'result/epoch{}budget{}_id{}.log'.format(epoch, budget, id)
    activefold = f'result/correlation_{id}'
    with open('Data/bgp-n_1000', 'r') as f:
        for line in f.readlines():
            prefixs.append(line.strip())
    # 多线程
    num_prefixs = len(prefixs)
    if num_thread != 1:
        prefixs = prefixs[(int(id))*num_prefixs//num_thread:(int(id)+1)*num_prefixs//num_thread]

    '''
    构建地址模式库
    '''
    # 将ipv6地址转换为需要的格式，例如2a0206b80c0401a80000060490942804
    print('converting..')
    seeds = convert(input_path)
    # 区域聚合，挖掘高密度区域
    print('Region Cluster..')
    Leaves = Region_cluster(seeds, delta)
    for leaf in Leaves:
        leaf.w = ["".join(leaf.w[i]) for i in range(leaf.size)]

    # 去除游离点，形成更高密度区域
    print('Remove outliers..')
    new_Leaves = []
    new_outliers = []
    with tqdm(total=len(Leaves)) as pbar:
        for leaf in Leaves:
            if leaf.size == 1:
                pbar.update(1)
                continue
            # 游离点去除
            new_patterns, outliers = OutlierDetect(leaf, 3)
            new_Leaves.extend(new_patterns)
            new_outliers.extend(outliers)
            pbar.update(1)
    
    for _ in range(3):
        # 区域聚合，挖掘高密度区域
        print('Region Cluster..')
        Leaves = Region_cluster(new_outliers, delta)
        for leaf in Leaves:
            leaf.w = ["".join(leaf.w[i]) for i in range(leaf.size)]

        # 去除游离点，形成更高密度区域
        print('Remove outliers..')
        new_outliers = []
        with tqdm(total=len(Leaves)) as pbar:
            for leaf in Leaves:
                if leaf.size == 1:
                    pbar.update(1)
                    continue
                # 游离点去除
                new_patterns, outliers = OutlierDetect(leaf, 3)
                new_Leaves.extend(new_patterns)
                new_outliers.extend(outliers)
                pbar.update(1)
    write_pattern(new_Leaves)

    """
    将模式与有种子bgp对应
    """
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
    with open('Data/bgp_with_patterns_clean.pkl','wb') as f:
        pkl.dump(bgp_with_patterns,f)

    with open('Data/bgp_with_patterns_clean.pkl','rb') as f:
        bgp_with_patterns = pkl.load(f)
    with open('Data/vocab.txt','r') as f:
        vocab = []
        for i in f.readlines():
            vocab.append(i)
    if os.path.exists(activefile):
        os.remove(activefile)
    if os.path.exists(targetfile):
        os.remove(targetfile)
    if os.path.exists(logfile):
        os.remove(logfile)
    if os.path.exists(activefold):
        shutil.rmtree(activefold)
    os.mkdir(activefold)
    
    for prefix in prefixs:
        print('BGP prefix:{}'.format(prefix))
        start = time.time()
        # 关联策略，得到有分数的bgp的排名，和没有分数的bgp的列表
        sorted_bgps = correlation(prefix,list(bgp_with_patterns.keys()),vocab) 
        current_budget = budget
        target = []
        pre_prescan_num = [0,0]

        totalpattern = gentotalPattern(prefix)
        if totalpattern.count('*') < 4:
            print('模式很小，全部生成')
            cache = genAddrByPattern(totalpattern, 0, spaceNum(totalpattern))
            target.extend(list(cache))
            active = Scan(target, ipv6, './', id)
            # 出口1：前缀能生成的地址很少，生成全部的
            if active:
                writeFile(target, active, targetfile, f'{activefold}/{inv_stdprefix_txt(prefix)}',mode=save_target)
            end = time.time()
            with open(logfile, 'a+') as f:
                f.write("\n#{},budget:{}\n".format(prefix, budget))
                f.write('target:{},active:{},hitrate:{},duration:{}\n'.format(
                    len(target), len(active), len(active)/len(target), end-start))
        else:
            # 存在有分数的bgp的情况
            if sorted_bgps[0][0]!=0:
                print('有分数')
                # 提取出这个分值的所有的bgp
                for score,top_bgps in sorted_bgps:
                    print(f'score:{score}'+'  '+f'length:{len(top_bgps)}')
                    # 如果有分值不是0，执行层次关联策略
                    if score !=0:
                        nodes = []
                        # 分数一样的bgp在一起考虑
                        for bgp in top_bgps:
                            nodes.extend(bgp_with_patterns[bgp])
                        margin = total_margin(nodes,prefix)
                        print(f'margin:{margin}')
                        with tqdm(total=current_budget) as pbar:
                            # 如果预算足够，先进行预探测，如果命中率足够高再生成
                            if margin < current_budget:
                                preScan_num = int(prescan_proportion*current_budget/miniBudget)
                                nodes_heapq, pre_target, pre_active = preScan(
                                        id, nodes, ipv6, preScan_num=preScan_num, miniBudget=miniBudget, activefile=f'{activefold}/{inv_stdprefix_txt(prefix)}', targetfile=targetfile)
                                hitrate = len(pre_active)/len(pre_target)
                                pre_prescan_num[0]+=len(pre_target)
                                pre_prescan_num[1]+=len(pre_active)
                                # current_budget-=(preScan_num*miniBudget)
                                current_budget-=len(pre_target)
                                pbar.update(len(pre_target))
                                if hitrate>=0:
                                    print('[+]Generate addresses..')
                                    for node in nodes_heapq:
                                        pbar.update(node.margin)
                                        cache = node.genAddr(node.margin, prescan=False)
                                        target.extend(list(cache)) # 计算margin时已经进行过前缀替换
                                        current_budget -= len(cache)
                            # 如果预算不够，先进行预探测，然后依次生成地址
                            else:
                                print('预算不够啦')
                                preScan_num = int(prescan_proportion*current_budget/miniBudget)
                                nodes_heapq, pre_target, pre_active = preScan(
                                        id, nodes, ipv6, preScan_num=preScan_num, miniBudget=miniBudget, activefile=f'{activefold}/{inv_stdprefix_txt(prefix)}', targetfile=targetfile)
                                if len(pre_target)!=0:
                                    hitrate = len(pre_active)/len(pre_target)
                                else:
                                    hitrate = 0
                                pre_prescan_num[0]+=len(pre_target)
                                pre_prescan_num[1]+=len(pre_active)
                                # current_budget-=(preScan_num*miniBudget)
                                current_budget-=len(pre_target)
                                pbar.update(len(pre_target))
                                if hitrate>0:
                                    print('正确率足够')
                                    print('[+]Generate addresses..')
                                    for node in nodes_heapq:
                                        if node.margin < current_budget:
                                            pbar.update(node.margin)
                                            cache = node.genAddr(node.margin, prescan=False)
                                            current_budget -= len(cache)
                                            target.extend(list(cache))
                                        else:
                                            pbar.update(current_budget)
                                            cache = node.genAddr(current_budget, prescan=False)
                                            target.extend(list(cache))
                                            current_budget = 0
                                            break
                                    end = time.time()
                                    # 出口2：预算在生成有分数bgp所属的模式时耗尽
                                    active = list(Scan(target, ipv6, './', id))
                                    if active:
                                        writeFile(target, active, targetfile, f'{activefold}/{inv_stdprefix_txt(prefix)}',mode=save_target)
                                    with open(logfile, 'a+') as f:
                                        f.write("\n#{},budget:{}\n".format(prefix, budget))
                                        f.write('target:{},active:{},hitrate:{},duration:{}\n'.format(
                                            len(target)+pre_prescan_num[0], len(active)+pre_prescan_num[1], (len(active)+pre_prescan_num[1])/(len(target)+pre_prescan_num[0]), end-start))
                                    break
                    else:
                        break

            # 预算仍未耗尽，沿用经典方法
            if current_budget > 0:
                active = list(Scan(target, ipv6, './', id))
                if active:
                    # 先把组织关联生成的target探测了
                    writeFile(target, active, targetfile, f'{activefold}/{inv_stdprefix_txt(prefix)}',mode=save_target)
                    print('还有预算')
                print("DHC方法生成")
                new_Leaves = []
                for bgp in sorted_bgps[-1][1]:
                    new_Leaves.extend(bgp_with_patterns[bgp])
                new_nodes = preprocess(new_Leaves, prefix)
                preScan_num = int(prescan_proportion*current_budget/miniBudget)
                batchsize = int((current_budget-preScan_num*miniBudget) / epoch)
                nodes_heapq, pre_target, pre_active = preScan(
                    id, new_nodes, ipv6, preScan_num=preScan_num, miniBudget=miniBudget, activefile=f'{activefold}/{inv_stdprefix_txt(prefix)}', targetfile=targetfile)
                target_num, active_num = scan_feedback2(
                    id, nodes_heapq, ipv6, batch_size=batchsize, epoch=epoch, targetfile=targetfile, activefile=f'{activefold}/{inv_stdprefix_txt(prefix)}')
                hitrate = (active_num+len(pre_active)+len(active)+pre_prescan_num[1]) / (target_num+len(pre_target)+len(target)+pre_prescan_num[0])
                end = time.time()
                with open(logfile, 'a+') as f:
                    f.write("\n#{},budget:{}\n".format(prefix, budget))
                    f.write('target:{},active:{},hitrate:{},duration:{}\n'.format(
                        target_num+len(pre_target)+len(target)+pre_prescan_num[0], active_num+len(pre_active)+len(active)+pre_prescan_num[1], hitrate, end-start))
                # print(nodes_heapq[0].new_pattern, nodes_heapq[0].hitrate)

if __name__ == "__main__":
    parse=argparse.ArgumentParser()
    parse.add_argument('--input_path', type=str, help='path of input IPv6 addresses')
    parse.add_argument('--IPv6',type=str,help='local IPv6 address')
    parse.add_argument('--budget',type=int,help='quantity of addresses detected by each BGP')
    parse.add_argument('--miniBudget',type=int, default=4, help='quantity of addresses detected by each BGP in prescan stage')
    parse.add_argument('--prescan_proportion',type=float, default=0.1, help='proportion of budget used in prescan stage')
    parse.add_argument('--epoch',type=int, default=12, help='number of dynamic scan rounds')
    parse.add_argument('--num_thread',type=int, default=1, help='number of threads')
    args=parse.parse_args()

    if args.num_thread == 0:
        main(args, 0, args.num_thread)
    else:
        thread = []
        for i in range(args.num_thread):
            thread.append(threading.Thread(name=f't{i}',target=main,args=(args, f'{i}', args.num_thread)))
        for i in range(args.num_thread):
            thread[i].start()
            time.sleep(1)

