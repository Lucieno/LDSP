#!/usr/bin/env python3

from threading import Thread, Lock, Event
from time import time
import timeit

from web3.auto import w3
from eth_account.messages import encode_defunct
from collections import deque

import sys
from concurrent import futures
from multiprocessing import Pool

import random
import grpc

import src_python.Offchaincommun.offchaincommun_pb2 as offchaincommun_pb2
import src_python.Offchaincommun.offchaincommun_pb2_grpc as offchaincommun_pb2_grpc

from src_python.Offchaincommun.utils import NamedTimerInstance, leader_argparser_distributed, PreSpend, \
    prespend_calc_left_right, ec_verify_sign_on_prespend, download_blindmsg_Y
from src_python.config import Config, ExpConfig
from src_python.Offchaincommun.libSchnorr import Schnorrsecp256k1, Schnorrbn128_leader
from src_python.mercus import merchant_setup
from src_python.coin import MerchantCoin

from src_python.ldsp_call import set_vk, set_epoch_index, get_leader_account, \
    single_withdrawal_blind_sign, ec_verify_customer_sign_withdraw, get_customer_account
from src_python.merkle import get_merkle_root
from src_python.solidity_helper import init_solidity, deploy_contract, get_contract, get_contract_account
from src_python.log_helper import Logger_OffchainCommun

from src_python.crypto_helper import multiply_g0, sum_g1
from py_ecc.bn128 import G1, G2
from py_eth_pairing import curve_add, curve_mul, curve_negate, pairing2


class LeaderBase:
    def __init__(self, vk, sk):
        self.lock = Lock()
        self.key_image_list = []
        self.leader_account = get_leader_account()
        self.customer_account = get_customer_account()
        self.vk = vk
        self.sk = sk


class LeaderPayment:
    def __init__(self, pool):
        self.web3_sk = "0x04b942fdf4242f30526fc17f20af27dc818550dd506f7241f795558594d76f80"
        self.pool = pool

    def ec_sign_prespend(self, prespend_lst):
        signatue_append = ""
        with NamedTimerInstance("Leader signing PreSpend"):
            for prespend in prespend_lst:
                prespend_encode = encode_defunct(text=prespend)
                signature = w3.eth.account.sign_message(prespend_encode, private_key=self.web3_sk).signature
                signatue_append += signature.hex() + " "
            signature_append = signatue_append.strip()
        return signature_append

    def batch_prespend_verify(self, prespend_lst):
        left_right = self.pool.map(prespend_calc_left_right, prespend_lst)
        sum_left = sum_g1(list(map(lambda x: x[0], left_right)))
        sum_right = sum_g1(list(map(lambda x: x[1], left_right)))
        return pairing2(curve_negate(sum_left), G2, sum_right, self.vk)


class LeaderWithdrawal:
    def __init__(self):
        self.merchant_sgn_lst = []
        self.num_sign = 0
        self.num_merchant = ExpConfig.num_merchant
        self.blinded_message = deque()
        self.event_obj = Event()
        self.challenge_idx = 2        
        self.timer = []

    def gen_merchant_coin(self, customer_id, num_coin):
        #if customer_id not in self.merchant_coin_lst:
        # clear previous record
        self.merchant_coin_lst = []
        random.seed(10)
        for i in range(num_coin):
            self.merchant_coin_lst.append(MerchantCoin(ExpConfig.epoch_index))
        random.seed()

    def single_blind_sign(self, customer_id):
        self.merchant_sgn_lst = []
        blindmsg_Y_lst = download_blindmsg_Y()
        blinded_message, Y = blindmsg_Y_lst[0]
        self.blinded_message.append(blinded_message)
        merchant_coin = self.merchant_coin_lst[0]
        sgn = merchant_coin.blind_sign(blinded_message, self.sk)
        self.merchant_sgn_lst.append(sgn)
        self.num_sign += 1
        if(self.num_sign == self.num_merchant):
            self.single_blind_sign_merge()

    def upload_blind_sgn_to_SC(self, blinded_sgn_lst):
        with open(Config.blind_sgn_path, 'w') as f:
            for blinded_sgn in blinded_sgn_lst:
                blinded_sgn_X, blinded_sgn_Y = blinded_sgn
                f.write("%d,%d;" %(blinded_sgn_X, blinded_sgn_Y))

    def single_blind_sign_merge(self):
        with NamedTimerInstance("Leader single merge BlindSign in Withdrawal"):
            print("merge BlindSign")
            blinded_coin = self.merchant_coin_lst[0].leader_blind_sign_merge(self.merchant_sgn_lst)
            if self.is_good_merchant is False:
                blinded_coin = curve_add(blinded_coin, G1)
            blinded_message = self.blinded_message.popleft()
            single_withdrawal_blind_sign(blinded_message, blinded_coin)
            self.upload_blind_sgn_to_SC([blinded_coin])
            self.num_sign = 0


class LeaderServicer(offchaincommun_pb2_grpc.OffchainCommunServicer, LeaderBase, LeaderPayment, LeaderWithdrawal):
    def __init__(self, vk, sk, merchant_sk, pool, is_good_merchant=True):
        LeaderBase.__init__(self, vk, sk)
        LeaderPayment.__init__(self, pool)
        LeaderWithdrawal.__init__(self)
        self.is_good_merchant = is_good_merchant
        self.merchant_sk = merchant_sk

    def ProcessPayment(self, request, context):
        with NamedTimerInstance("Leader receiving PreSpend to setting PreSpend"):
            PreSpend_correct = True
            PreSpend_ = request.prespend
            PreSpend_list = PreSpend_.split()
            verify_lst = []
            for prespend in PreSpend_list:
                prespend_ = PreSpend(prespend)
                if prespend_.validPreSpend is False:
                    return
                verify_lst.append(prespend_)

        with NamedTimerInstance("Leader verifying PreSpend"):
            prespend_valid = self.batch_prespend_verify(verify_lst)
        if prespend_valid is True:
            signature_ = self.ec_sign_prespend(PreSpend_list)
            yield offchaincommun_pb2.Signature(signature=signature_)
        sys.stdout.flush()

    def StartWithdrawal(self, request, context):
        self.prev_coin = 0
        self.curr_coin = ExpConfig.num_coin_batch

        with NamedTimerInstance("Leader generate MerchantCoin in Withdrawal"):
            num_coin_total = request.num_coin
            self.gen_merchant_coin(request.customer_id, num_coin_total)

        self.fund_id = int(request.fund_id)

        if num_coin_total > 1:
            self.merchant_sgn_lst = [[] for i in range(num_coin_total)]

        with NamedTimerInstance("Leader setting Y to sending in Withdrawal"):
            batch_Y = ""
            num_round = ExpConfig.num_coin_total // ExpConfig.num_coin_batch
            for round_idx in range(num_round):
                prev_coin = round_idx * ExpConfig.num_coin_batch
                curr_coin = prev_coin + ExpConfig.num_coin_batch
                for merchant_coin in self.merchant_coin_lst[prev_coin:curr_coin]:
                    Y_prime_X, Y_prime_Y = merchant_coin.Y
                    batch_Y += "%d,%d" %(Y_prime_X, Y_prime_Y) + ";"
                batch_Y = batch_Y.strip(";")
                yield offchaincommun_pb2.Y(Y=batch_Y)
                batch_Y = ""

        self.num_sign = 0

        if num_coin_total == 1:
            with NamedTimerInstance("Leader single blind sign in Withdrawal"):
                self.single_blind_sign(request.customer_id)

    def SingleBlindSignMerge(self, request, context):
        merchant_sgn = request.signature
        sgn_X, sgn_Y  = merchant_sgn.split(';')
        self.merchant_sgn_lst.append((int(sgn_X), int(sgn_Y)))
        self.num_sign += 1

        if(self.num_sign == self.num_merchant):
            self.single_blind_sign_merge()
        return offchaincommun_pb2.Empty()

    def BatchBlindSignM2L(self, request, context):
        self.timer.append(timeit.default_timer())
        merchant_sgn = request.signature
        merchant_sgn_lst  = merchant_sgn.split(';')
        for idx, sgn in enumerate(merchant_sgn_lst):
            sgn_X, sgn_Y  = sgn.split(',')
            self.merchant_sgn_lst[idx].append((int(sgn_X), int(sgn_Y)))
        self.num_sign += 1
        if(self.num_sign == self.num_merchant):
            self.event_obj.set()
        #sys.stdout.flush()
        return offchaincommun_pb2.Empty()

    def BatchWithdrawC2L(self, request, context):
        #print("Time for starting BatchWithdrawC2L", timeit.default_timer())
        self.timer.append(timeit.default_timer())
        with NamedTimerInstance("Leader handles Customer signature in Withdrawal"):
            customer_id = request.customer_id
            signature = request.signature
            blind_sn = request.blind_sn
            Y = request.Y_sgn
            blind_sn_lst = blind_sn.split(';')
            blind_sn_lst = [int(bld_sn) for bld_sn in blind_sn_lst]
            Y_lst = Y.split(';')
            Y_lst_ = []
            for y in Y_lst:
                Y_prime_X, Y_prime_Y = y.split(',')
                Y_lst_.append((int(Y_prime_X), int(Y_prime_Y)))

        with NamedTimerInstance("Leader computes MHTRoot in Withdrawal"):
            blind_sn_y_hash, _ = get_merkle_root([[blind_sn_lst[i], Y_lst_[i][0], Y_lst_[i][1]] for i in range(ExpConfig.num_coin_batch)])

        with NamedTimerInstance("Leader verifies Customer signature in Withdrawal"):
            res = ec_verify_customer_sign_withdraw(self.prev_coin, self.curr_coin, signature, blind_sn_y_hash, self.customer_account)

        if(res):
            merchant_mergesgn_lst = []
            merchant_mergesgn = ""
            with NamedTimerInstance("Leader blind signs in Withdrawal"):
                for idx, (merchant_coin, blind_sn) in enumerate(zip(self.merchant_coin_lst[self.prev_coin:self.curr_coin], blind_sn_lst)):
                    signature = merchant_coin.blind_sign(blind_sn, self.sk)
                    self.merchant_sgn_lst[idx].append(signature)
            self.num_sign += 1
            #print("c2l+1=", self.num_sign)
            if(self.num_sign < self.num_merchant):
                self.event_obj.wait() # wait until receiving signatures from other merchants
            #print("Time for broadcast at leader:", time_for_broadcast, "ms  Timer:", self.timer)
            time_for_broadcast = (timeit.default_timer() - self.timer[0]) * (10 ** 3)
            print("Time for Leader Receiving First Request to Finishing all Requests:", time_for_broadcast, "ms")
            self.num_sign = 0
            self.timer = []
            with NamedTimerInstance("Leader merge signs in Withdrawal"):
                for (merchant_coin, merchant_sgn) in zip(self.merchant_coin_lst[self.prev_coin:self.curr_coin], self.merchant_sgn_lst):
                    merge_sign = merchant_coin.leader_blind_sign_merge(merchant_sgn)
                    merchant_mergesgn_lst.append(merge_sign)
            if(self.is_good_merchant is False):
                merchant_mergesgn_lst[self.challenge_idx] = curve_add(blinded_coin[self.challege_idx], G1)
            with NamedTimerInstance("Leader send signatures to customer in Withdrawal"):
                for merge_sign in merchant_mergesgn_lst:
                    merge_sign_X, merge_sign_Y = merge_sign
                    merchant_mergesgn += str(merge_sign_X) + ',' + str(merge_sign_Y) + ';'
                merchant_mergesgn = merchant_mergesgn.strip(';')
                sd_sign = offchaincommun_pb2.Signature(signature=merchant_mergesgn)
                yield sd_sign
            sys.stdout.flush()
            self.prev_coin += ExpConfig.num_coin_batch
            self.curr_coin += ExpConfig.num_coin_batch
            self.merchant_sgn_lst = [[] for i in range(ExpConfig.num_coin_total)]
            self.event_obj.clear()
            

if __name__ == "__main__":
    port = leader_argparser_distributed()
    account = init_solidity()
    contract = deploy_contract(account)
    random.seed(10)
    merchant_sk, vk = merchant_setup()    
    random.seed()
    set_vk(vk)
    set_epoch_index()

    test = "payment"
    processpool = None

    if test == "payment":
        processpool = Pool(4)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=ExpConfig.num_merchant))
    offchaincommun_pb2_grpc.add_OffchainCommunServicer_to_server(LeaderServicer(vk, merchant_sk[0], merchant_sk, processpool), server)
    print('Leader listening on port', port)
    sys.stdout = Logger_OffchainCommun("leader")
    server.add_insecure_port('[::]:'+str(port))
    server.start()
    server.wait_for_termination()
