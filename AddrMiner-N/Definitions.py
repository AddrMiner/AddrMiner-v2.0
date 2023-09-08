from tools import genAddrByPattern, genList, getStdprefix, listReverse, numConversion, str2ipv6,hamming
import math

BASE = ['0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']


class Node(object):
    def __init__(self, seeds: list, genpattern=True):
        self.w = seeds
        self.pattern = ""
        self.hitrate = 0  # 累积命中率
        self.new_pattern = ""  # 替换成无种子地址前缀后的新模式
        self.cache = set()  # 每一次生成的目标地址
        self.target = set()  # 所有生成过的目标地址
        self.active_num = 0  # 探测到的活跃地址数量
        self.hash_value = hash(self.pattern)
        self.margin = 0  # 地址余量

        self.size = len(self.w)  # 区域种子个数
        self.pattern_freeDim = 0  # 本身模式的所有free dimension个数
        self.new_pattern_freeDim = 0  # 替换模式的所有free dimension个数

        if genpattern:
            self.updatePattern()

    def __hash__(self):
        return self.hash_value

    def __eq__(self, other: object):
        return self.hash_value == other.hash_value

    def __lt__(self, other: object):
        if self.hitrate != other.hitrate:
            return self.hitrate > other.hitrate
        else:  # 相等情况优先考虑高密度区域
            return self.npdensity() > other.npdensity()

    def pdensity(self):
        """
        原区域真实密度
        """
        if self.pattern_freeDim == 0:
            return 0
        else:
            return math.log(16, self.size) - self.pattern_freeDim + 31.75

    def pdensity2(self):
        """
        原区域另一种密度表示
        """
        if self.pattern_freeDim == 0:
            return 0
        else:
            return self.size / self.pattern_freeDim

    def npdensity(self):
        """
        新区域真实密度
        """
        if self.new_pattern_freeDim == 0:
            return 0
        else:
            return math.log(16, self.size) - self.new_pattern_freeDim + 31.75

    def updatePattern(self):
        self.pattern = ""
        RS = listReverse(self.w)
        # 查看种子集中每个维度的情况
        for dim in range(32):
            tmp = set(RS[dim])
            if len(tmp) == 1:
                self.pattern += RS[dim][0]
            else:
                self.pattern += "*"
        self.hash_value = hash(self.pattern)
        self.pattern_freeDim = self.pattern.count('*')

    def addSeed(self, addr):
        """
        加入一个种子地址到区域中
        """
        self.w.append(addr)
        self.size += 1
        self.updatePattern()

    def delSeed(self, addr):
        """
        删除一个种子地址
        """
        self.w.remove(addr)
        self.size -= 1
        self.updatePattern()

    def prefixReplace(self, prefix: str):
        """
        替换前缀，返回新模式
        """
        prefixLen = int(prefix.split('/')[1])
        stdPrefix = getStdprefix(prefix)
        self.new_pattern = ""
        if stdPrefix[-1] == "]":
            self.new_pattern += stdPrefix
            self.new_pattern += self.pattern[int(prefixLen/4)+1:]
        else:
            self.new_pattern += stdPrefix[:int(prefixLen/4)]
            self.new_pattern += self.pattern[int(prefixLen/4):]

        self.new_pattern_freeDim = self.new_pattern.count('*')
        self.hash_value = hash(self.new_pattern)

        return self.new_pattern
    
    def hammingDistance(self):
        hamming(self.pattern,self.new_pattern)


    def genAddr(self, num, prescan=False):
        """
        按照模式顺序生成一定数量地址
        Args:
            num: 生成地址数量
            prescan: 是否为预探测
        """
        newPattern = self.new_pattern
        if prescan:
            self.target.clear()
            self.active_num = 0
            self.init_margin()
            
        self.cache.clear()

        if self.margin == 0:
            return set()
        genNum = min(num, self.margin)  # 此次生成的地址数量
        # print(num,self.margin)
        self.cache = genAddrByPattern(newPattern, len(self.target), genNum)
        self.target = self.cache | self.target
        self.margin -= genNum
        if self.margin < 0:
            print('calculate margin error!')
        return self.cache

    def init_margin(self):
        self.margin = 0
        if '[' in self.new_pattern:
            li_l = self.new_pattern.index('[')
            li_r = self.new_pattern.index(']')
            li = genList(self.new_pattern[li_l+1], self.new_pattern[li_r-1])
            self.margin = int(math.pow(16, self.new_pattern_freeDim))*len(li)
        else:
            self.margin = int(math.pow(16, self.new_pattern_freeDim))
