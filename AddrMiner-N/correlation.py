import json
import pickle as pkl
import os
from tqdm import tqdm

def stdprefix(name:str):
    """
    将json文件名转化为IPv6地址
    Args:
        name:文件名
    """
    try:
        a,b = name.split('...')
        pre = a.split('.')
        pre = ':'.join(pre)
        prefix = pre+'::/'+b[:-5]
    except:
        a,b = name.split('.._')
        pre = a.split('.')
        pre = ':'.join(pre)
        prefix = pre+'::/'+b[:-5]
    return prefix

def inv_stdprefix(stdpre:str):
    """
    将IPv6地址转化为json文件名
    Args:
        stdpre:IPv6地址
    """
    if stdpre!=None:
        try:
            a,b = stdpre.split('::/')
            pre = '.'.join(a.split(':'))
            name1 = pre+'...'+b+'.json'
            name2 = pre+'...'+'json'
            name3 = pre+'.._'+b+'.json'
            return (name1,name2,name3)
        except:
            return ('','','')
    else:
        return ('','','')

def inv_stdprefix_txt(stdpre:str):
    try:
        a,b = stdpre.split('::/')
        pre = '.'.join(a.split(':'))
        name1 = pre+'...'+b+'.txt'
        return name1
    except:
        a,b = stdpre.split('/')
        name1 = a+'...'+b+'.txt'
        return name1

def find_whois(bgp:str):
    """
    查找给定bgp对应的whois文件
    Args:
        bgp:给定bgp
    """
    if os.path.isfile(f'whois/{inv_stdprefix(bgp)[0]}'):
        try:
            with open(f'whois/{inv_stdprefix(bgp)[0]}','r') as a:
                whois = json.load(a)
                try:
                    return whois['country'],whois['org'],whois['ipdescr']
                except:
                    return '','',''
        except:return '','',''
    elif os.path.isfile(f'whois/{inv_stdprefix(bgp)[1]}'):
        try:
            with open(f'whois/{inv_stdprefix(bgp)[1]}','r') as a:
                whois = json.load(a)
                try:
                    return whois['country'],whois['org'],whois['ipdescr']
                except:
                    return '','',''
        except:return '','',''
    elif os.path.isfile(f'whois/{inv_stdprefix(bgp)[2]}'):
        try:
            with open(f'whois/{inv_stdprefix(bgp)[2]}','r') as a:
                whois = json.load(a)
                try:
                    return whois['country'],whois['org'],whois['ipdescr']
                except:
                    return '','',''
        except:return '','',''
    else:
        return '','',''

def correlation(bgp_n:str,bgps:list,vocab:list):
    """
    多层关联策略
    Args:
        bgp_n:无种子bgp
        bgps:有种子bgp列表
        vocab:关键词列表
    """
    scores_with_bgp = {}
    countryn,orgn,descrn = find_whois(bgp_n)
    for bgp in bgps:
        score = 0
        country,org,descr = find_whois(bgp)
        # 优先级匹配
        if org==orgn and org!='' and org!= None:score+=2
        if country==countryn and country!='' and country!=None:score+=1
        for word in vocab:
            try:
                if (word in descr) and (word in descrn):
                        score+=0.5
            except:
                continue
        if score not in scores_with_bgp:scores_with_bgp[score]=[]
        scores_with_bgp[score].append(bgp)
    sorted_bgps = sorted(scores_with_bgp.items(),key=lambda top_bgps:top_bgps[0],reverse=True)
    return sorted_bgps
            

if __name__ == '__main__':
    prefixs = []
    with open('pk_data/bgp_with_patterns','rb') as f:
        bgp_with_patterns = pkl.load(f)
    with open('pk_data/vocab.txt','r') as f:
        vocab = []
        for i in f.readlines():
            vocab.append(i)
    with open('BGP/bgp_n_with_whois-removeAliasPrefix', 'r') as f:
        for line in f.readlines():
            prefixs.append(line.strip())
    with tqdm(total=len(prefixs)) as pbar:
        for prefix in prefixs[:4]:
            # prefix = '2404:e800::/31'
            print('BGP prefix:{}'.format(prefix))
            # 关联策略，得到有分数的bgp的排名，和没有分数的bgp的列表
            sorted_top_bgps, bottom_bgps = correlation(prefix,list(bgp_with_patterns.keys()),vocab) 
            # print(sorted_top_bgps)
            print(len(sorted_top_bgps))
            pbar.update(1)
            for item in sorted_top_bgps:
                print(item[1])
