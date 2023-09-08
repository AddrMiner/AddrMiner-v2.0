

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





