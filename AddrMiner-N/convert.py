def convert(path):
    result = []
    with open(path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            line = line.split(":")

            for i in range(len(line)):
                if len(line[i]) == 4:
                    continue
                if len(line[i]) < 4 and len(line[i]) > 0:
                    zero = "0"*(4 - len(line[i]))
                    line[i] = zero + line[i]
                if len(line[i]) == 0:
                    zeros = "0000"*(9 - len(line))
                    line[i] = zeros
            result.append("".join(line)[:32])

    return result

def write(output_path, data):
    with open(output_path,'w') as f:
        for item in data:
            f.write(item+'\n')


if __name__ == "__main__":
    path = "Data/responsive-addresses.txt"
    data = convert(path)
    write('Data/normalization_new.txt',data)
