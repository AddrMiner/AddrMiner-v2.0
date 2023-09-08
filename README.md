# AddrMiner-v2.0
AddrMiner-v2.0 is an improved global active IPv6 address detection system based on AddrMiner-v1.0. The specific improvements encompass two aspects: On the one hand, it simplifies the address detection architecture by dividing address detection into two detection scenarios(seedless address scenario<=>AddrMiner-N, and seeded address scenario<=>AddrMiner-S), making it more practical for deployment. On the other hand, it introduces a multi-level association policy (MLAP) to enhance further the coverage and resource utilization of seedless regional detection.


## Dependencies and installation
AddrMiner-S is compateible with Python3.x. You can install the requirements for your version. Besides, RDET uses the following packages:
 
* argparse
```
pip3 install argparse
```

## zmapv6 installation (ask in IPv4 network)

###  Building from Source

```
git clone https://github.com/tumi8/zmap.git
cd zmap
```
### Installing ZMap Dependencies

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

### Building and Installing ZMap

```
cmake .
make -j4
sudo make install
```

## Usage
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
# Data
In order to support IPv6 network related research, we provide more data about hitlist(active IPv6 addresses) and address fingerprint information.

If you want more data, you can send a request to 18231535@bjtu.edu.cn 

The request should include the work department, the purpose of data usage, and the data content obtained.





