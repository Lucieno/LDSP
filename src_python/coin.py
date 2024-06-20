from json import JSONEncoder
import random
from copy import deepcopy
from typing import List, Tuple

from sympy.stats import Coin
from web3 import Web3
import sympy
from py_ecc.bn128 import multiply, add, G1, G2

from py_eth_pairing import curve_negate, curve_mul, curve_add, pairing2

from src_python.config import Config
from src_python.curve_helper import hash_to_g1, hash_to_int, g1_to_int
from src_python.crypto_helper import multiply_g0, sum_g1, add_g0
from src_python.bench_helper import CodeTimer


def get_hash_sn(sn):
    return hash_to_int(sn)


class MerchantCoin(object):
    def __init__(self, t):
        # CHY BlindSign Part 1
        self.gamma = random.randint(1, Config.curve_order)
        self.C = hash_to_g1(t)
        self.Y = curve_mul(self.C, self.gamma)

    def blind_sign(self, blinded_message, bls_key_sk) -> Tuple[int, int]:
        # CHY BlindSign Part 2
        # Si = (ski m') * C + ski * Y = (m' + gamma) ski * C
        g0_order = multiply_g0(add_g0(blinded_message, self.gamma), bls_key_sk)
        return curve_mul(self.C, g0_order)

    def blind_sign_merge(self, blinded_message, sk_lst) -> Tuple[int, int]:
        S = [self.blind_sign(blinded_message, sk) for sk in sk_lst]
        return merge_bls_sign(S)

    def leader_blind_sign_merge(self, S):
        return merge_bls_sign(S)


def merge_bls_sign(sign_lst) -> Tuple[int, int]:
    assert (len(sign_lst) >= 1)
    return sum_g1(sign_lst)


class CustomerCoin(object):
    coin = None

    def __init__(self, t, Y):
        self.Y = deepcopy(Y)
        self.t = deepcopy(t)

        self.blind()

    def blind(self):
        # CHY PartBlind
        self.sn = random.randint(1, Config.sn_order)
        self.hashed_sn = get_hash_sn(self.sn)

        self.alpha = random.randint(1, Config.curve_order)
        self.beta = random.randint(1, Config.curve_order)
        self.Y_prime = curve_add(
            curve_mul(self.Y, self.alpha),
            curve_mul(hash_to_g1(self.t), multiply_g0(self.alpha, self.beta)))

        Y_prime_X, Y_prime_Y = g1_to_int(self.Y_prime)

        self.hpmy = hash_to_int([self.hashed_sn, Y_prime_X, Y_prime_Y])

        # self.hpmy = hash_to_int(
        #     Web3.toBytes(hexstr=hex(self.hashed_sn))
        #     + Web3.toBytes(hexstr=hex(Y_prime_X))
        #     + Web3.toBytes(hexstr=hex(Y_prime_Y)))

        self.alpha_inverse = sympy.mod_inverse(self.alpha, Config.curve_order)

        # puzzle
        self.blinded_message = (multiply_g0(self.alpha_inverse, self.hpmy) + self.beta) % Config.curve_order

    def calc_left_right(self, blinded_sign, is_random_exp=False):
        S = blinded_sign
        C = hash_to_g1(self.t)
        right = curve_add(curve_mul(C, self.blinded_message), self.Y)

        if is_random_exp:
            left, right = exp_randomize(S, right)
            return S, left, right

        return S, right

    def verify_blind(self, S, right, vk):
        return pairing2(curve_negate(S), G2, right, vk)

    def unblind_without_verify(self, S):
        S_prime = curve_mul(S, self.alpha)
        sign = (S_prime, self.Y_prime)
        self.coin = Coin(self.t, self.sn, sign)
        return self.coin

    def unblind(self, blinded_sign, vk):
        # CHY Unblind
        # if the blinded_sign well-formed?
        # e(S', g2) ?= e(m' C + Y, vk)
        S, right = self.calc_left_right(blinded_sign)
        assert (self.verify_blind(S, right, vk))
        return self.unblind_without_verify(S)


def batch_unblind(cus_coin_lst: List[CustomerCoin], blinded_lst: List[Tuple[int, int]], vk):
    S_left_right = [cus_coin_lst[i].calc_left_right(blinded_lst[i], is_random_exp=True) for i in
                    range(len(blinded_lst))]
    S = list(map(lambda x: x[0], S_left_right))
    sum_left = sum_g1(list(map(lambda x: x[1], S_left_right)))
    sum_right = sum_g1(list(map(lambda x: x[2], S_left_right)))

    assert (pairing2(curve_negate(sum_left), G2, sum_right, vk))

    return [cus_coin_lst[i].unblind_without_verify(S[i]) for i in range(len(blinded_lst))]


def get_commitment_lst(customer_coin: List[CustomerCoin]):
    lst = []
    for x in customer_coin:
        Y = g1_to_int(x.Y)
        lst.append([Y[0], Y[1], x.blinded_message])
    return lst


class Coin(object):
    def __init__(self, t, sn, sign):
        self.sn = deepcopy(sn)
        self.t = deepcopy(t)
        self.sign = deepcopy(sign)

    def calc_left_right(self, is_random_exp=False):
        # left: S', right: Y' + hp(m, Y') * H(t)
        S_prime, Y_prime = self.sign
        Y_prime_X, Y_prime_Y = g1_to_int(Y_prime)
        hashed_sn = get_hash_sn(self.sn)
        C = hash_to_g1(self.t)

        hpmy = hash_to_int([hashed_sn, Y_prime_X, Y_prime_Y])
        # hpmy = hash_to_int(Web3.toBytes(hexstr=hex(hashed_sn))
        #                    + Web3.toBytes(hexstr=hex(Y_prime_X))
        #                    + Web3.toBytes(hexstr=hex(Y_prime_Y)))

        right = curve_add(curve_mul(C, hpmy), Y_prime)

        if is_random_exp:
            S_prime, right = exp_randomize(S_prime, right)

        return S_prime, right

    def verify(self, vk):
        # CHY verify
        left, right = self.calc_left_right()

        pairing_test = pairing2(curve_negate(left), G2, right, vk)

        return pairing_test


def batch_coin_verify(coin_lst: List[Coin], vk):
    left_right = [x.calc_left_right(is_random_exp=True) for x in coin_lst]
    sum_left = sum_g1(list(map(lambda x: x[0], left_right)))
    sum_right = sum_g1(list(map(lambda x: x[1], left_right)))

    return pairing2(curve_negate(sum_left), G2, sum_right, vk)


def exp_randomize(left, right):
    random_exp = random.randint(1, Config.random_exp_order)
    left = curve_mul(left, random_exp)
    right = curve_mul(right, random_exp)
    return left, right


def bls_sign_to_lst(sign):
    S, Y = sign
    return [int(S[0]), int(S[1]), int(Y[0]), int(Y[1])]
