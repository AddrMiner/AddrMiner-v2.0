# AddrMiner-v2.0
AddrMiner-v2.0 is an improved global active IPv6 address detection system based on AddrMiner-v1.0. The specific improvements encompass two aspects: On the one hand, it simplifies the address detection architecture by dividing address detection into two detection scenarios(seedless address scenario<=>AddrMiner-N, and seeded address scenario<=>AddrMiner-S), making it more practical for deployment. On the other hand, it introduces a multi-level association policy (MLAP) to enhance further the coverage and resource utilization of seedless regional detection.




## AddrMiner-S
### Dependencies and installation
AddrMiner-S is compateible with Python3.x. You can install the requirements for your version. Besides, RDET uses the following packages:
 
* argparse
```
pip3 install argparse
```

### zmapv6 installation (ask in IPv4 network)

####  Building from Source

```
git clone https://github.com/tumi8/zmap.git
cd zmap
```
#### Installing ZMap Dependencies

On Debian-based systems (including Ubuntu):
```
sudo apt-get install build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev
```

On RHEL- and Fedora-based systems (including CentOS):
```
sudo yum install cmake gmp-devel gengetopt libpcap-devel flex byacc json-c-devel libunistring-devel
```

On macOS systems (using Homebrew):
```
brew install pkg-config cmake gmp gengetopt json-c byacc libdnet libunistring
```

#### Building and Installing ZMap

```
cmake .
make -j4
sudo make install
```

### Usage
Parameter meaning introduction：
* input:  type=str, input IPv6 addresses
* output: type=str,output directory name
* budget: type=int,the upperbound of scan times
* IPv6:   type=str,local IPv6 address
* delta:  type=int, default =16, the base of address
* beta:   type=int, default=16,the max of node
* alpha:  type=float, default=0.1,learning rate
* num_node: type=int, default=100
* batch_size: type=int, default=1000
running example
```
sudo python3 DynamicScan.py
```





# AddrMiner-N

Integrated solution for IPv6 address discovery. This project utilizes *whois* information corresponding to BGP to analyze the correlation between seedless BGP and seeded BGP, solving the difficulty of IPv6 address discovery for seedless BGP.

## Dependencies

### Language and packages

AddrMiner-N uses python3. You may install the required packages through the following command:

```
pip3 install -r requirements.txt
```

### zmapv6 installation(ask in IPv4 network)

#### Building from Source

```
git clone https://github.com/tumi8/zmap.git
cd zmap
```

#### Installing ZMap Dependencies

On Debian-based systems (including Ubuntu):

```
sudo apt-get install build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev
```

On RHEL- and Fedora-based systems (including CentOS):

```
sudo yum install cmake gmp-devel gengetopt libpcap-devel flex byacc json-c-devel libunistring-devel
```

On macOS systems (using Homebrew):

```
brew install pkg-config cmake gmp gengetopt json-c byacc libdnet libunistring
```

#### Building and Installing ZMap

```
cmake .
make -j4
sudo make install
```

## Usage

### Files

| File            | Introduction                               |
| --------------- | ------------------------------------------ |
| DynamicScan.py  | Main entrance of the project               |
| Definitions.py  | The model of patterns                      |
| rangeCluster.py | Density clustering algorithm for addresses |
| tools.py        | Functions used in the project              |
| correlation.py  | Multi-level Association Policy             |
| convert.py      | IPv6 address standardization               |
| rmoutlier.py    | Method for removing outliers               |
| find.py         | Other functions                            |

### Data

Input data is contained in the *Data* folder, and *whois* information is contained in the *whois* folder.

Please note that we have only provided a portion of the seed addresses and *whois* information. For full data, please obtain it from other channels.

| file                 | Introduction             |
| -------------------- | ------------------------ |
| Data/seeds_10000.txt | 10000 seed addresses     |
| Data/ipasn.dat       | asn information of BGP   |
| Data/vocab.txt       | Used in MLAP             |
| Data/bgp-n_1000      | 1000 seedless BGP        |
| whois/*certain BGP*  | whois information of BGP |

### **Parameters**

- input_path: type=str, path of input IPv6 addresses
- IPv6: type=str, local 
- budget: type=int, quantity of addresses detected by each BGP
- miniBudget: type=int, default=4, quantity of addresses detected by each BGP in prescan stage
- prescan_proportion: type=float, default=0.1, proportion of budget used in prescan stage
- epoch: type=int, default=12, number of dynamic scan rounds
- num_thread: type=int, default=1, number of threads

### Example

```
sudo python3 DynamicScan.py --input_path=Data/seeds_10000.txt --budget=10000  --IPv6=your local IPv6 address
```


## Data
Data Access: https://addrminer.github.io/IPv6_hitlist.github.io/#

To support IPv6 network-related research, we provide more data about hitlist(active IPv6 addresses) and address fingerprint information.

If you want more data, you can send a request to songgl@mail.zgclab.edu.cn

The request should include the work department, the purpose of data usage, and the data content obtained.





