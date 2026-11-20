def print_list(l):
    for line in l:
        print(line)

def reorder_by_urdf(names: list[str], angles: list[float]) -> list[float]:
    return [angles[names.index("t")], angles[names.index("s")], angles[names.index("e")], angles[names.index("wp")], angles[names.index("wr")], angles[names.index("g")]]