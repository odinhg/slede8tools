import argparse

def bytecode_to_asm(b1, b2, max_len, labels):
    opclass = b1 & 0x0f
    if opclass == 0x00:
        return "STOPP"
    if opclass == 0x01:
        reg = (0xf0 & b1) >> 4
        if reg <= 15:
            return "SETT r{0}, {1}".format(str(reg), hex(b2))
    if opclass == 0x02:
        reg1, reg2 = (0xf0 & b1) >> 4, b2 & 0x0f
        if reg1 <= 15 and reg2 <= 15:
            return "SETT r{0}, r{1}".format(str(reg1), str(reg2))
    if opclass == 0x03:
        adr = (b2 << 4) | ((b1 & 0xf0) >> 4)
        if adr <= max_len:
            return "FINN {0}".format(labels[adr])
    if opclass == 0x04:
        reg = b2 & 0x0f
        if reg <= 15:
            if (b1 & 0xf0) >> 4:
                return "LAGR r{0}".format(str(reg))
            else:
                return "LAST r{0}".format(str(reg))
    if opclass == 0x05:
        op = (b1 & 0xf0) >> 4
        reg1, reg2 = b2 & 0x0f, (b2 & 0xf0) >> 4
        oplabels = ["OG", "ELLER", "XELLER", "VSKIFT", "HSKIFT", "PLUSS", "MINUS"]
        if op <= len(oplabels) and reg1 <= 15 and reg2 <= 15:
            return "{0} r{1}, r{2}".format(oplabels[op], str(reg1), str(reg2))
    if opclass == 0x06:
        reg = b2
        if reg <= 15:
            if (b1 & 0xf0) >> 4:
                return "SKRIV r{0}".format(str(reg))
            else:
                return "LES r{0}".format(str(reg))
    if opclass == 0x07:
        op = (b1 & 0xf0) >> 4
        reg1, reg2 = b2 & 0x0f, (b2 & 0xf0) >> 4
        oplabels = ["LIK", "ULIK", "ME", "MEL", "SE", "SEL"]
        if op <= len(oplabels) and reg1 <= 15 and reg2  <= 15:
            return "{0} r{1}, r{2}".format(oplabels[op], str(reg1), str(reg2))
    if 0x08 <= opclass <= 0x0a:
        adr = (b2 << 4) | ((b1 & 0xf0) >> 4)
        oplabels = ["HOPP", "BHOPP", "TUR"]
        if adr <= max_len:
            return "{0} {1}".format(oplabels[opclass-0x08], labels[adr])
    if opclass == 0x0b:
        return "RETUR"
    if opclass == 0x0c:
        return "NOPE"
    return "; Unknown operation {0} {1}".format(hex(b1), hex(b2))

def find_data_and_branches(binary):
    max_len = len(binary)
    entry_points = []
    branch_points = []
    labels = {}
    data_cnt, branch_cnt = 0, 0
    for ptr in range(0, len(binary)):
        opclass = binary[ptr] & 0x0f
        if opclass in [0x08, 0x09, 0x0a]: # HOPP, BHOPP or TUR op
            adr = (binary[ptr+1] << 4) | ((binary[ptr] & 0xf0) >> 4)
            if adr <= max_len:
                branch_points.append(adr)
                if adr not in labels.keys():    
                    labels[adr] = "Branch{0}".format(str(branch_cnt))
                branch_cnt += 1
        elif opclass == 0x03: # FINN op
            adr = (binary[ptr+1] << 4) | ((binary[ptr] & 0xf0) >> 4)
            if adr <= max_len:
                entry_points.append(adr)
                if adr not in labels.keys():    
                    labels[adr] = "DataBlock{0}".format(str(data_cnt))
                data_cnt += 1
        else:
            continue
    
    print("\n; Labels:")
    for p in [*entry_points, *branch_points]:
        print("; {0:#05x} - {1}".format(p, labels[p]))
    
    entry_points = sorted(entry_points)
    branch_points.append(len(binary))
    branch_points = sorted(branch_points)

    print("\n; Guessed data segments:")
    data_blobs = []
    for p in entry_points:
        for q in branch_points:
            if q-p > 0:
                print("; \t *{0:#05x} to {1:#05x} data block of length {2}.".format(p,q-1, q-p))
                data_blobs += [i for i in range(p,q)]
                break
    return labels, data_blobs

# SLEDE8 DISASSEMBLER
parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str, help="SLEDE8 binary filename")
args = parser.parse_args()

with open(args.filename, "rb") as bin_file:
    binary = bin_file.read()
if binary[:7].decode("ascii") != ".SLEDE8":
    print("Filetype error.")
else:
    binary = binary[7:]
    labels, data_blobs = find_data_and_branches(binary)
    print("\n;SLEDE8 BEGIN")
    pc = 0x00
    while(pc < len(binary)):
        if pc in labels:
            print("\n{0}:".format(labels[pc]))
        if pc in data_blobs: # print data blob
            print(".DATA ", end="")
            while pc in data_blobs:
                print(hex(binary[pc]), end="")
                if pc+1 in data_blobs:
                    print(", ", end="")
                pc += 1
                if pc in labels.keys():
                    break
            print()
        else:
            print(bytecode_to_asm(binary[pc], binary[pc+1], len(binary), labels))
            pc += 2
    print(";SLEDE8 END")
