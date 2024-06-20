import socket
import argparse
from time import time, sleep
import os
import timeit
import random
from threading import Thread
from typing import List

from web3.auto import w3
from eth_account.messages import encode_defunct

from src_python.config import ExpConfig, Config
from py_ecc.bn128 import multiply, add, G1, G2
from py_eth_pairing import curve_negate, curve_mul, curve_add, pairing2
from src_python.curve_helper import hash_to_g1, hash_to_int, g1_to_int
from src_python.coin import exp_randomize
from src_python.crypto_helper import multiply_g0, sum_g1, add_g0

#from libSchnorr import Schnorrsecp256k1

def benchmark_argparser_distributed():
    default_ip = ""
    num_test = 1
    defualt_test = "withdrawal"
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="HostAddr",
                        default=default_ip,
                        help="The Master Address for communication")
    parser.add_argument("--coin",
                        dest="num_coin",
                        default=ExpConfig.num_coin_total,
                        help="Number of coins")
    parser.add_argument("--num_test",
                        dest="num_test",
                        default=num_test,
                        help="Number of tests")
    parser.add_argument("--test",
                        dest="test",
                        default=defualt_test,
                        help="Type of test")
    args = parser.parse_args()
    HostAddr = socket.gethostbyname(args.HostAddr)
    num_coin = int(args.num_coin)
    num_test = int(args.num_test)

    return HostAddr, num_coin, num_test, args.test

def customer_argparser_distributed():
    default_ip = ""
    default_port = "33200"
    default_mode = "n"
    default_merchantid = gen_random_ID()
    default_customerid = gen_random_ID()
    default_num_test = 1
    default_test = "withdrawal"

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="HostAddr",
                        default=default_ip,
                        help="The Master Address for communication")
    parser.add_argument("--port",
                        dest="Port",
                        default=default_port,
                        help="The Master Port for communication")
    parser.add_argument("--num_test",
                        dest="num_test",
                        default=default_num_test,
                        help="The number of the experiment")
    parser.add_argument("--test",
                        dest="test",
                        default=default_test,
                        help="Type of the experiment")
    parser.add_argument("--MID",
                        dest="MerchantID",
                        default=default_merchantid,
                        help="MerchantID")
    parser.add_argument("--CID",
                        dest="CustomerID",
                        default=default_customerid,
                        help="CustomerID")
    parser.add_argument("--coin",
                        dest="num_coin",
                        default=ExpConfig.num_coin_total,
                        help="Number of coins")
    args = parser.parse_args()
    HostAddr = socket.gethostbyname(args.HostAddr)
    Port = args.Port
    num_test = int(args.num_test)
    MerchantID = int(args.MerchantID)
    CustomerID = int(args.CustomerID)
    num_coin = int(args.num_coin)
    return HostAddr, Port, MerchantID, CustomerID, num_coin, num_test, args.test

def merchant_argparser_distributed():
    default_ip = ""
    default_port = "33150"
    default_listen_port = "33200"
    default_id = gen_random_ID()
    default_test = "payment"
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        dest="HostAddr",
                        default=default_ip,
                        help="The Master Address for communication")
    parser.add_argument("--port",
                        dest="Port",
                        default=default_port,
                        help="The Master Port for communication")
    parser.add_argument("--Mport",
                        dest="MPort",
                        default=default_listen_port,
                        help="The port for listen")
    parser.add_argument("--ID",
                        dest="ID",
                        default=default_id,
                        help="ID")
    parser.add_argument("--test",
                        dest="test",
                        default=default_test,
                        help="test name")
    args = parser.parse_args()
    HostAddr = socket.gethostbyname(args.HostAddr)
    Port = args.Port
    MPort = args.MPort
    ID = int(args.ID)
    return HostAddr, Port, MPort, ID, args.test

def leader_argparser_distributed():
    default_ip = ""
    default_port = "33150"
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",
                        dest="Port",
                        default=default_port,
                        help="The Master Port for communication")
    args = parser.parse_args()
    Port = args.Port
    return Port

def parser_argparser_distributed():
    default_test = "withdrawal"
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",
                        dest="test",
                        default=default_test,
                        help="The LDSP operation")
    args = parser.parse_args()
    Port = args.Port
    return Port

def find_latency_bandwidth():
    result = os.popen("tc q").read()
    result = result.split()
    latency = "-1"
    bandwidth = "-1"
    if "delay" in result:
        idx = result.index("delay") + 1
        latency = result[idx]
    if "rate" in result:
        idx = result.index("rate") + 1
        bandwidth = result[idx]
    return latency, bandwidth

def print_setting(num_coin, num_test, test):
    latency, bandwidth = find_latency_bandwidth()
    if test == "withdrawal":
        print("================= Testing %s %d times with %d coin (batch size %d) under latency %s bandwidth %s with %d merchants =================" % (test, num_test, num_coin, ExpConfig.num_coin_batch, latency, bandwidth, ExpConfig.num_merchant))
    else:
        print("================= Testing %s %d times with %d coin under latency %s bandwidth %s with %d merchants =================" % (test, num_test, num_coin, latency, bandwidth, ExpConfig.num_merchant))

def gen_random_ID(num_participants=10):
    return random.randint(0, num_participants - 1)

class Timer(object):
    def __init__(self, name):
        self.name = name
        self.t0 = timeit.default_timer()
        self.t1 = None

    def start(self):
        self.t0 = timeit.default_timer()

    def show_time(self):
        print("Time for " + self.name+":", (self.t1 - self.t0) * (10 ** 3), "ms")

    def end(self, is_show_time=None):
        self.t1 = timeit.default_timer()
        if True:
            self.show_time()

class NamedTimer(object):
    __instance = None

    @staticmethod
    def get_instance():
        if NamedTimer.__instance is None:
            NamedTimer()
        return NamedTimer.__instance

    def __init__(self):
        NamedTimer.__instance = self
        self.timers = {}

    @staticmethod
    def start(name, **kwargs):
        NamedTimer.get_instance().timers[name] = Timer(name, **kwargs)
        return NamedTimer.get_instance().timers[name]

    @staticmethod
    def end(name):
        NamedTimer.get_instance().timers[name].end()

class NamedTimerInstance(object):
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        return NamedTimer.start(self.name)

    def __exit__(self, *args):
        NamedTimer.end(self.name)

class PreSpend(object):
    def __init__(self, prespend):
        try:
            S_prime_X, S_prime_Y, Y_prime_X, Y_prime_Y, hashed_sn, t = prespend.split(',')
            self.S_prime = (int(S_prime_X), int(S_prime_Y))
            self.Y_prime = (int(Y_prime_X), int(Y_prime_Y))
            self.hashed_sn = int(hashed_sn)
            self.t = int(t)
            self.validPreSpend = True
        except:
            print("Error in PreSpend")
            self.validPreSpend = False

    def calc_left_right(self, is_random_exp=False):
        Y_prime_X, Y_prime_Y = g1_to_int(self.Y_prime)
        C = hash_to_g1(self.t)
        hpmy = hash_to_int([self.hashed_sn, Y_prime_X, Y_prime_Y])
        right = curve_add(curve_mul(C, hpmy), self.Y_prime)

        if is_random_exp:
            S_prime, right = exp_randomize(self.S_prime, right)

            return S_prime, right
        return self.S_prime, right

def prespend_calc_left_right(prespend):
    return prespend.calc_left_right(is_random_exp=True)

def batch_prespend_verify(left_right, vk):
    sum_left = sum_g1(list(map(lambda x: x[0], left_right)))
    sum_right = sum_g1(list(map(lambda x: x[1], left_right)))

    return pairing2(curve_negate(sum_left), G2, sum_right, vk)

def ec_verify_sign_on_prespend(signed_prespend, prespend, leader_account):
    prespend_encode = encode_defunct(text=prespend)
    addr = w3.eth.account.recover_message(prespend_encode, signature=signed_prespend)
    return (addr == leader_account)

def download_blindmsg_Y():
    sleep(1)
    while(not os.path.exists(Config.blindmsg_Y_path)):
        print(Config.blindmsg_Y_path, "is not here")
        sleep(1)
    with open(Config.blindmsg_Y_path, 'r') as f:
        blindmsg_Ys = f.read()
    blindmsg_Y_lst = blindmsg_Ys.strip(';').split(';')
    blindmsg_Y_lst_ = []
    for blindmsg_Y in blindmsg_Y_lst:
        blindmsg, Y_prime_X, Y_prime_Y = blindmsg_Y.split(',')
        blindmsg_Y_lst_.append((int(blindmsg), (int(Y_prime_X), int(Y_prime_Y))))
    return blindmsg_Y_lst_

if __name__ == "__main__":
    string = "4232334325572065716279090931524910179555293474845395083612990832779992464401,4921029797847701208511954810633299966158885838347527051382522687960782015235,7612264067057716203343254550063512344602498149072748862862648277356131327611,5218106010854165122513665453299388555899507374404649441070619923109335764843,25438592770268254416861644140926502678290648738030805729671365195464962638563,4232"
    prespend = PreSpend(string)
