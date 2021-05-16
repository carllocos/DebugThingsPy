single_callstack = [1, 4, 5, 8, 16, 32, 64, 128]
double_callstack=  [128, 200, 220, 230, 240, 245]
out = "measurements.txt"

def measure(fn:str):
    print("===============================")
    print(f"file {fn}")
    with open(fn, 'r') as file:
        lines = file.readlines()
        callstack_size = None
        total_time = 0
        min_time = 500
        max_time = 0
        quantity = 0
        for l in lines:
            # print(f"line {l}")
            if l == '\n':
                print("skipping line")
                break

            [time, cs, _] = l.split(",")
            callstack_size = int(cs.split(":")[1])
            _t = float(time.split(":")[1])
            if _t > max_time:
                max_time = _t
            if _t < min_time:
                min_time = _t

            total_time +=_t
            quantity += 1

        if quantity != 0:
            avg_time = total_time / quantity
            obj = {
                'avg': avg_time,
                'max': max_time,
                'min': min_time,
                'cs_size': callstack_size,
            }
            print(obj)
            return [avg_time, max_time, min_time, callstack_size]
        else:
            print("READDDD no measurement")

def register_measure(fn, fac_arg):
        [avg, max_time, min_time, cs_size ] = measure(fn)
        s = f"fac_arg: {i}, callstack_size: {cs_size}, avg: {avg} max: {max_time} min: {min_time}\n"
        print(s)
        f = open(out , "a")
        f.write(s)
        f.close()

def register_header(max_cs):
    f = open(out , "a")
    f.write(f"MAX_CALLSTACK {max_cs}\n")
    f.close()


if __name__ == "__main__":
    register_header(int("0x100", 16))
    for i in single_callstack:
        fn = "bench_fac_" + str(i) + ".txt"
        register_measure(fn, i)

    register_header(int("0x200", 16))
    for i in double_callstack:
        fn = "double_bench_fac_" + str(i) + ".txt"
        register_measure(fn, i)
            