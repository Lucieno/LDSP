from copy import copy

from src_python.curve_helper import hash_to_bytes32
from src_python.math_helper import roundup_power_2


def get_merkle_root(lst):
    n = len(lst)
    cnt = roundup_power_2(n)
    curr_hash = [hash_to_bytes32(x) for x in lst]
    curr_hash += [hash_to_bytes32(0) for _ in range(n, cnt)]

    acc_hash = copy(curr_hash)
    while (cnt > 1):
        cnt //= 2
        curr_hash = [hash_to_bytes32([curr_hash[2 * i], curr_hash[2 * i + 1]])
                     for i in range(cnt)]
        acc_hash = curr_hash + acc_hash
    return acc_hash[0], acc_hash


def get_merkle_proof(elem_idx, num_elem, saved_hash=None, lst=None):
    assert (elem_idx < num_elem)
    if saved_hash is None and lst is None:
        raise Exception("need either saved_hash or lst")
    if saved_hash is None:
        _, saved_hash = get_merkle_root(lst)
    res = []
    running_idx = (roundup_power_2(num_elem) - 1) + elem_idx
    while running_idx > 0:
        if running_idx % 2 == 0:  # is right
            res.append(saved_hash[running_idx - 1])
        else:
            res.append(saved_hash[running_idx + 1])
        running_idx = (running_idx - 1) // 2
    return res


def verify_merkle_proof(elem_idx, elem, proof, root):
    running_idx = elem_idx
    leaf = hash_to_bytes32(elem)
    for i in range(len(proof)):
        if running_idx % 2 == 0:  # is left
            leaf = hash_to_bytes32([leaf, proof[i]])
        else:
            leaf = hash_to_bytes32([proof[i], leaf])
        running_idx //= 2
    return leaf == root
