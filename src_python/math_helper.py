def roundup_power_2(x):
    # https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-172-performance-engineering-of-software-systems-fall-2018/lecture-slides/MIT6_172F18_lec3.pdf
    res = 1
    while res < x:
        res *= 2
    return res


def roundup_log_2(x):
    res = 1
    while (2 ** res) < x:
        res += 1
    return res
