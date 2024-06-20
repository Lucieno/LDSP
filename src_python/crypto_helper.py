from copy import deepcopy

from py_ecc.bn128 import add
from py_eth_pairing import curve_add

from src_python.config import Config


def multiply_g0(a, b):
    return (a * b) % Config.curve_order


def add_g0(a, b):
    return (a + b) % Config.curve_order


def sum_g0(iter) -> object:
    return sum(iter) % Config.curve_order


def sum_g1(lst):
    res = deepcopy(lst[0])
    for x in lst[1:]:
        res = curve_add(res, x)
    return res


def sum_g2(lst):
    res = deepcopy(lst[0])
    for x in lst[1:]:
        res = add(res, x)
    return res
