import string
from functools import lru_cache

from _pysha3 import keccak_256
from py_ecc import bn128
from eth_abi.packed import encode_single_packed, encode_abi_packed

from py_eth_pairing import curve_mul


def g2_to_int_lst(pt):
    return [int(pt[0].coeffs[1]), int(pt[0].coeffs[0]), int(pt[1].coeffs[1]), int(pt[1].coeffs[0])]


def g1_to_int(x):
    return int(x[0]), int(x[1])


def is_hex_str(x):
    if isinstance(x, str) is False or x[:2] != "0x":
        return False
    return all(c in string.hexdigits for c in x[2:])


def type_convert(x):
    if isinstance(x, int):
        return 'uint', x
    elif is_hex_str(x):
        if len(x) == 42:
            return 'address', x
        else:
            return 'uint', int(x, 16)
    elif isinstance(x, bytes):
        # print(len(x), x)
        if len(x) == 32:
            return 'bytes32', x
        return 'bytes', x
    # elif isinstance(x, str):
    #     return 'bytes', x.encode()
    else:
        # print(x)
        raise Exception(f"Not supporting: {type(x)}")


def get_packed_encoding(lst):
    # https://docs.soliditylang.org/en/latest/abi-spec.html#non-standard-packed-mode
    # tmp = single_encoding(x)
    # n = len(tmp)
    # padded_n = (n // 32 + ((n % 32) != 0)) * 32
    # return tmp.rjust(padded_n, b'\00')

    # https://eth-abi.readthedocs.io/en/latest/encoding.html
    if isinstance(lst, list) is False:
        lst = [lst]
    type_lst = []
    value_lst = []
    for x in lst:
        if isinstance(x, (list, tuple)):
            for item in x:
                t, v = type_convert(item)
                type_lst.append(t)
                value_lst.append(v)
        else:
            t, v = type_convert(x)
            type_lst.append(t)
            value_lst.append(v)
    # print(type_lst, value_lst)
    return encode_abi_packed(type_lst, value_lst)


def hash_encode(message, is_binary=False):
    k = keccak_256()
    k.update(get_packed_encoding(message))
    if is_binary:
        return k.digest()
    return k.hexdigest()


def hash_to_bytes32(message):
    return hash_encode(message, is_binary=True)

def hash_to_int(message):
    return int(hash_encode(message), 16)


@lru_cache(maxsize=32)
def hash_to_g1(message):
    return curve_mul(bn128.G1, int(hash_encode(message), 16))
