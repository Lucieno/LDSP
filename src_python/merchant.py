import random
import json

from py_ecc.fields import bn128_FQ2
from py_eth_pairing import curve_mul, curve_add
from py_ecc.bn128 import multiply, add, G1, G2

from src_python.config import Config, ExpConfig
from src_python.session import store_obj, load_obj, is_store_path_exist
from src_python.crypto_helper import sum_g0, sum_g2, sum_g1


class BlsKey(object):
    sk, pk1, pk2 = None, None, None

    def __init__(self):
        return

    def generate(self):
        self.sk = random.randint(1, Config.curve_order)
        self.pk1 = curve_mul(G1, self.sk)
        self.pk2 = multiply(G2, self.sk)

    def get_pk(self):
        return (self.pk1, self.pk2)

    def get_vk(self):
        return self.pk2

    def __repr__(self):
        return str(self.__dict__)

    def to_json(self):
        # print("type(self.pk1)", type(self.pk1))
        # print("type(self.pk1[0])", type(self.pk1[0]))
        # print("type(self.pk1[1])", type(self.pk1[1]))
        # print("type(self.pk2[0])", type(self.pk2[0]))
        # print("type(self.pk2[1])", type(self.pk2[1]))
        # print("self.pk2[0].coeffs[0]", type(self.pk2[0].coeffs[0]), self.pk2[0].coeffs[0], )
        res = {'sk': self.sk,
               'pk10': self.pk1[0],
               'pk11': self.pk1[1],
               'pk200': int(self.pk2[0].coeffs[0]),
               'pk201': int(self.pk2[0].coeffs[1]),
               'pk210': int(self.pk2[1].coeffs[0]),
               'pk211': int(self.pk2[1].coeffs[1]),
               }
        return res

    @classmethod
    def from_json(cls, json_str):
        res = cls()
        d = json.loads(json_str, object_hook=dict)
        res.sk = int(d['sk'])
        res.pk1 = (int(d['pk10']), int(d['pk11']))
        res.pk2 = (bn128_FQ2((int(d['pk200']), int(d['pk201']))), bn128_FQ2((int(d['pk210']), int(d['pk211']))))
        return res


def merge_bls_key(bls_key_lst):
    assert (len(bls_key_lst) >= 1)
    merged_key = BlsKey()
    merged_key.sk = sum_g0(list(map(lambda x: x.sk, bls_key_lst)))
    merged_key.pk1 = sum_g1(list(map(lambda x: x.pk1, bls_key_lst)))
    merged_key.pk2 = sum_g2(list(map(lambda x: x.pk2, bls_key_lst)))
    return merged_key


def generate_merchant_key(num_merchant):
    merchant_key = [BlsKey() for i in range(num_merchant)]
    for x in merchant_key:
        x.generate()
    merged_key = merge_bls_key(merchant_key)
    return merchant_key, merged_key


def store_all_merchant_key(merchant_key, merged_key):
    for i, x in enumerate(merchant_key):
        store_obj("merchant_key_%02d" % i, x)
    store_obj("merged_key", merged_key)
    store_obj("merchant_key_meta", {"num_merchant": len(merchant_key)})


def load_all_merchant_key():
    meta = load_obj("merchant_key_meta", dict)
    num_merchant = meta["num_merchant"]
    assert (num_merchant == ExpConfig.num_merchant)
    merchant_key = [load_obj("merchant_key_%02d" % i, BlsKey) for i in range(num_merchant)]
    merged_key = load_obj("merged_key", BlsKey)
    return merchant_key, merged_key


def is_merchant_key_stored():
    return is_store_path_exist("merchant_key_meta")


def load_or_gen_merchant_key(num_merchant, is_forced=ExpConfig.force_merchant_key_generation):
    if is_forced or is_merchant_key_stored() is False:
        print("Generating Merchant Keys")
        merchant_key, merged_key = generate_merchant_key(num_merchant)
        store_all_merchant_key(merchant_key, merged_key)
    else:
        print("Loading Existing Merchant Keys")
        merchant_key, merged_key = load_all_merchant_key()
        assert (len(merchant_key) == num_merchant)
    return merchant_key, merged_key


if __name__ == "__main__":
    generate_merchant_key(ExpConfig.num_merchant)
