from random import randint

import sympy
from py_eth_pairing import curve_mul, curve_add

from src_python.crypto_helper import multiply_g0
from src_python.curve_helper import hash_to_int, hash_to_bytes32, hash_to_g1, g1_to_int
from src_python.coin import MerchantCoin, CustomerCoin
from src_python.config import ExpConfig, Config
from src_python.math_helper import roundup_power_2, roundup_log_2


def generate_seg_key():
    return randint(1, Config.seg_key_max)


def encrypt_opening(alpha, beta, hashed_sn, key) -> object:
    enc_alpha = alpha ^ hash_to_int([key, 0])
    enc_beta = beta ^ hash_to_int([key, 1])
    enc_hashed_sn = hashed_sn ^ hash_to_int([key, 2])
    return enc_alpha, enc_beta, enc_hashed_sn
    # return key, key, key


def decrypt_opening(enc, key):
    # alpha, beta, hashed_sn
    return encrypt_opening(enc[0], enc[1], enc[2], key)


def encrypt_customer_coin(customer_coin: CustomerCoin, key):
    return encrypt_opening(customer_coin.alpha, customer_coin.beta, customer_coin.hashed_sn,
                           key)


def get_num_key(num_coin):
    n_padded = roundup_power_2(num_coin)
    return (n_padded - 1) + num_coin


def generate_all_seg_key(num_coin):
    num_key = get_num_key(num_coin)
    return [generate_seg_key() for _ in range(num_key)]


def encrypt_all_customer_coin(customer_coin):
    num_coin = len(customer_coin)
    num_layer = roundup_log_2(num_coin) + 1
    # print("num_coin, num_layer:", num_coin, num_layer)
    key = generate_all_seg_key(num_coin)

    def encrypt_coin_lst(k, lst):
        return [encrypt_customer_coin(c, k) for c in lst]

    enc_coin = [encrypt_coin_lst(key[0], customer_coin)]
    # n_padded = roundup_power_2(num_coin)
    itrv = roundup_power_2(num_coin)
    for i in range(1, num_layer):
        tmp_enc = []
        itrv //= 2
        offset_key = 2 ** i - 1
        # num_layer_key =  n_padded // itrv
        for j in range(num_coin):
            remain_key_idx = j // itrv
            key_idx = offset_key + remain_key_idx
            k = key[key_idx]
            tmp_enc.append(encrypt_customer_coin(customer_coin[j], k))
        enc_coin.append(tmp_enc)
    return key, enc_coin[::-1]


def seg_locate(coin_idx, left, right, n):
    # res = []
    saved_input = (coin_idx, left, right, n)

    left += n - 1
    right += n - 1
    coin_idx += n - 1
    key_idx, layer_idx = 0, 0
    while left > 0 and right > 0 and left < right:
        if is_right(left):
            # res.append(left)
            if coin_idx == left:
                return key_idx, layer_idx
            key_idx += 1;
            left += 1
        left = to_parent(left)

        if is_left(right):
            # res.append(right)
            if coin_idx == right:
                return key_idx, layer_idx
            key_idx += 1
            right -= 1
        right = to_parent(right)

        layer_idx += 1
        coin_idx = to_parent(coin_idx)

    if left == right:
        return key_idx, layer_idx
        key_idx += 1
        # res.append(left)

    raise Exception("seg_locate: outside of left/right bound", saved_input)


def is_right(x):
    return x % 2 == 0


def is_left(x):
    return x % 2 == 1


def to_parent(x):
    return (x - 1) // 2


def verify_single_opening(cmt, enc_opening, revealing_key):
    Y0, Y1, blind_msg = cmt
    Y = (Y0, Y1)
    # print("enc_opening", enc_opening)
    # print("enc_opening, revealing_key", enc_opening[0], revealing_key)
    alpha, beta, hashed_sn = decrypt_opening(enc_opening, revealing_key)

    Y_prime = curve_add(
        curve_mul(Y, alpha),
        curve_mul(hash_to_g1(ExpConfig.epoch_index), multiply_g0(alpha, beta)))

    Y_prime_X, Y_prime_Y = g1_to_int(Y_prime)
    hpmy = hash_to_int([hashed_sn, Y_prime_X, Y_prime_Y])
    alpha_inverse = sympy.mod_inverse(alpha, Config.curve_order)
    recon_blind_msg = (multiply_g0(alpha_inverse, hpmy) + beta) % Config.curve_order

    return (recon_blind_msg == blind_msg)


def verify_batch_opening(cmt, enc_opening, revealing_key, left_bound, right_bound, num_coin):
    offset = roundup_power_2(num_coin) - 1
    left = left_bound + offset
    right = right_bound + offset
    key_idx, layer_idx = 0, 0

    wrong_idx = []

    def verify_subtree(running_key_idx, key_layer_idx, running_layer_idx, running_idx):
        if running_layer_idx == 0:
            coin_idx = running_idx - offset
            enc_idx = key_layer_idx * num_coin + coin_idx
            verify_res = verify_single_opening(
                cmt[coin_idx], enc_opening[enc_idx], revealing_key[running_key_idx])
            if verify_res is False:
                wrong_idx.append(coin_idx)
        else:
            verify_subtree(running_key_idx, key_layer_idx, running_layer_idx - 1, 2 * running_idx + 1)
            verify_subtree(running_key_idx, key_layer_idx, running_layer_idx - 1, 2 * running_idx + 2)

    while left > 0 and right > 0 and left < right:
        if is_right(left):
            verify_subtree(key_idx, layer_idx, layer_idx, left)
            key_idx += 1
            left += 1
        left = to_parent(left)

        if is_left(right):
            verify_subtree(key_idx, layer_idx, layer_idx, right)
            key_idx += 1
            right -= 1
        right = to_parent(right)

        layer_idx += 1

    if left == right:
        verify_subtree(key_idx, layer_idx, layer_idx, left)

    return wrong_idx


def select_reveal_key(key, num_coin, left_bound, right_bound):
    left = left_bound + num_coin - 1
    right = right_bound + num_coin - 1
    res = []

    while left > 0 and right > 0 and left <= right:
        if is_right(left):
            res.append(key[left])
            left += 1
        left = to_parent(left)
        if is_left(right):
            res.append(key[right])
            right -= 1
        right = to_parent(right)
    if left == right:
        res.append(key[left])

    return res


if __name__ == "__main__":
    merchant_coin = MerchantCoin(ExpConfig.epoch_index)
    customer_coin = CustomerCoin(ExpConfig.epoch_index, merchant_coin.Y)

    seg_key = generate_seg_key()
    enc_opening = encrypt_customer_coin(customer_coin, seg_key)
    print(enc_opening)
