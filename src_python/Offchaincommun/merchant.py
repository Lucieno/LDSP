#!/usr/bin/env python3

import sys
import os
from time import time
import timeit
import random
from concurrent import futures
import grpc
import src_python.Offchaincommun.offchaincommun_pb2 as offchaincommun_pb2
import src_python.Offchaincommun.offchaincommun_pb2_grpc as offchaincommun_pb2_grpc

from multiprocessing import Pool

from src_python.crypto_helper import multiply_g0, sum_g1
from py_eth_pairing import curve_negate, pairing2
from py_ecc.bn128 import G2

from web3.auto import w3
from eth_account.messages import encode_defunct

from src_python.Offchaincommun.utils import merchant_argparser_distributed, NamedTimerInstance, PreSpend, \
    prespend_calc_left_right, ec_verify_sign_on_prespend, download_blindmsg_Y
from src_python.config import ExpConfig
from src_python.mercus import merchant_setup
from src_python.coin import MerchantCoin
from src_python.ldsp_call import get_leader_account, get_customer_account, ec_verify_customer_sign_withdraw
from src_python.merkle import get_merkle_root
from src_python.solidity_helper import init_solidity, get_contract
from src_python.log_helper import Logger_OffchainCommun


class MerchantBase:
    def __init__(self, leader_ip, port, merchant_id, pool):
        self.merchant_id = merchant_id
        self.create_stub_for_leader(leader_ip, port)
        self.leader_account = get_leader_account()
        self.customer_account = get_customer_account()
        self.pool = pool

    def create_stub_for_leader(self, leader_ip, port):
        arr = leader_ip + ":" + port
        channel = grpc.insecure_channel(arr)
        self.stub = offchaincommun_pb2_grpc.OffchainCommunStub(channel)

    def batch_prespend_verify(self, prespend_lst):
        #print("merchant len of verify_lst", len(prespend_lst))
        left_right = self.pool.map(prespend_calc_left_right, prespend_lst)

        sum_left = sum_g1(list(map(lambda x: x[0], left_right)))
        sum_right = sum_g1(list(map(lambda x: x[1], left_right)))
        return pairing2(curve_negate(sum_left), G2, sum_right, self.vk)


class MerchantTimeBase:
    def __init__(self):
        self.time_list = {}
        for i in range(400):
            self.time_list[i] = []

    def timer(self, customer_id):
        self.time_list[customer_id].append(timeit.default_timer())

    def show_time(self, name, t1, t0):
        print("Time for " + name+":", (t1 - t0) * (10 ** 3), "ms")

    def show_time_list(self):
        pop_list = []
        for customer_id, tlist in self.time_list.items():
            if(len(tlist) < 5):
                continue
            self.show_time("Merchant receiving to setting PreSpend", tlist[1], tlist[0])
            self.show_time("Merchant verifying PreSpend", tlist[2], tlist[1])
            self.show_time("Merchant setting MerchantPayInfo", tlist[3], tlist[2])
            self.show_time("Merchant sending MerchantPayInfo to receiving and saving Signature", tlist[4], tlist[3])
            self.show_time("Merchant verifying and sending Signature", tlist[5], tlist[4])
            self.show_time("Merchant sending Signature to receiving Solution", tlist[6], tlist[5])
            pop_list.append(customer_id)
        for customer_id in pop_list:
            self.time_list.pop(customer_id)
        sys.stdout.flush()
        self.time_idx += 1


class MerchantPayment:
    def verify_sign_on_prespend(self, signed_prespend, prespend):
        prespend_encode = encode_defunct(text=prespend)
        addr = w3.eth.account.recover_message(prespend_encode, signature=signed_prespend)
        return (addr == self.leader_account)


class MerchantWithdrawal(MerchantBase):
    def __init__(self, leader_ip, port, merchant_id,  num_coin, sk):
        MerchantBase.__init__(self, leader_ip, port, merchant_id)
        self.merchant_coin_lst = {}
        self.sk = sk
        self.gen_merchant_coin(num_coin)

    def gen_merchant_coin(self, num_coin):
        #if customer_id not in self.merchant_coin_lst:
        #    self.merchant_coin_lst[customer_id] = []
        self.merchant_coin_lst = []
        random.seed(10)
        for i in range(num_coin):
            self.merchant_coin_lst.append(MerchantCoin(ExpConfig.epoch_index))
        random.seed()

    def single_blind_sign(self):
        blindmsg_Y_lst = download_blindmsg_Y()
        blinded_message, Y = blindmsg_Y_lst[0]
        merchant_coin = self.merchant_coin_lst[0]

        with NamedTimerInstance("Merchant%d blind signing in Withdrawal" %(self.merchant_id)):
            sgn = merchant_coin.blind_sign(blinded_message, self.sk)

        with NamedTimerInstance("Merchant%d setting S_%d in Withdrawal" %(self.merchant_id, self.merchant_id)):
            sgn_X, sgn_Y = sgn
            merchant_S = "%d;%d" % (sgn_X, sgn_Y)
            request = offchaincommun_pb2.MerchantSignature(merchant_id=self.merchant_id, signature=merchant_S)

        with NamedTimerInstance("Merchant%d sending S_%d in Withdrawal to receiving acknowledgement" %(self.merchant_id, self.merchant_id)):
            #self.stub.SingleBlindSignMerge(request)
            response = self.stub.SingleBlindSignMerge(request)

class MerchantBatchWithdrawal:
    def __init__(self, num_coin, sk):
        self.merchant_coin_lst = []
        self.sk = sk
        self.prev_coin = 0
        self.curr_coin = ExpConfig.num_coin_batch
        self.gen_merchant_coin(num_coin)
        self.executor = futures.ThreadPoolExecutor(max_workers = 4)

    def gen_merchant_coin(self, num_coin):
        #if customer_id not in self.merchant_coin_lst:
        #    self.merchant_coin_lst[customer_id] = []
        self.merchant_coin_lst = []
        random.seed(10)
        for i in range(num_coin):
            self.merchant_coin_lst.append(MerchantCoin(ExpConfig.epoch_index))
        random.seed()

    def handle_withdraw_request(self, signature, blind_sn, Y):
        with NamedTimerInstance("Merchant Parse Customer Request in Withdrawal"):
            blind_sn_lst = blind_sn.split(';')
            blind_sn_lst = [int(bld_sn) for bld_sn in blind_sn_lst]
            Y_lst = Y.split(';')
            Y_lst_ = []
            for y in Y_lst:
                Y_prime_X, Y_prime_Y = y.split(',')
                Y_lst_.append((int(Y_prime_X), int(Y_prime_Y)))
        with NamedTimerInstance("Merchant computes MHTRoot in Withdrawal"):
            blind_sn_y_hash, _ = get_merkle_root([[blind_sn_lst[i], Y_lst_[i][0], Y_lst_[i][1]] for i in range(ExpConfig.num_coin_batch)])
        with NamedTimerInstance("Merchant verifies Customer signature in Withdrawal"):
            res = ec_verify_customer_sign_withdraw(self.prev_coin, self.curr_coin, signature, blind_sn_y_hash, self.customer_account)
        if(res):
            merchant_sign = ""
            with NamedTimerInstance("Merchant signing in Withdrawal"):
                for merchant_coin, blind_sn in zip(self.merchant_coin_lst[self.prev_coin:self.curr_coin], blind_sn_lst):
                    sgn_X, sgn_Y = merchant_coin.blind_sign(blind_sn, self.sk)
                    merchant_S = "%d,%d" % (sgn_X, sgn_Y)
                    merchant_sign += merchant_S + ";"
                merchant_sign = merchant_sign.strip(';')
                sd_sign = offchaincommun_pb2.MerchantSignature(merchant_id=self.merchant_id, signature=merchant_sign)
            with NamedTimerInstance("Merchant sends sign to Leader in Withdrawal"):
                self.stub.BatchBlindSignM2L(sd_sign) # send signature to leader
        self.prev_coin += ExpConfig.num_coin_batch
        self.curr_coin += ExpConfig.num_coin_batch
        if self.prev_coin == ExpConfig.num_coin_total:
            self.prev_coin = 0
            self.curr_coin = ExpConfig.num_coin_batch
        sys.stdout.flush()


class MerchantServicer(offchaincommun_pb2_grpc.OffchainCommunServicer, MerchantBase, MerchantPayment, MerchantBatchWithdrawal, MerchantTimeBase):
    def __init__(self, leader_ip, port, merchant_id, vk, sk="-1", pool=None):
        MerchantBase.__init__(self, leader_ip, port, merchant_id, pool)
        MerchantTimeBase.__init__(self)
        MerchantBatchWithdrawal.__init__(self, ExpConfig.num_coin_total, sk)       
        self.port = port
        self.vk = vk
        self.customers_lists = {}
        self.time_idx = 1

    def StartPayment(self, request, context):
        customer_id = request.customer_id
        self.timer(self.time_idx) # receiving PreSpend
        PreSpend_ = request.prespend
        PreSpend_list = PreSpend_.split()
        verify_lst = []
        for prespend in PreSpend_list:
            prespend_ = PreSpend(prespend)
            if prespend_.validPreSpend is False:
                return
            verify_lst.append(prespend_)
        self.timer(self.time_idx) # after setting Prespend
        prespend_valid = self.batch_prespend_verify(verify_lst)
        self.timer(self.time_idx) # after verifying Prespend
        if prespend_valid is False:
            return
        merchantpayinfo = offchaincommun_pb2.MerchantPayInfo(merchant_id=self.merchant_id, prespend=PreSpend_)
        signature = ""
        self.timer(self.time_idx) # sending PreSpend
        response_iterator = self.stub.ProcessPayment(merchantpayinfo)
        for response in response_iterator:
            signature = response.signature
        signature_lst = signature.split()
        self.timer(self.time_idx) # receiving Signature
        if customer_id not in self.customers_lists:
            self.customers_lists[customer_id] = []
        self.customers_lists[customer_id].append(PreSpend_)
        valid_sgn = True
        for sgn, prespend in zip(signature_lst, PreSpend_list):
            verify_result = self.verify_sign_on_prespend(sgn, prespend)
            valid_sgn = (valid_sgn and verify_result)
        self.timer(self.time_idx) # sending Signature
        if valid_sgn:
            self.customers_lists[customer_id].append(signature)
            yield response

    def TransmitPuzSol(self, request, context):
        customer_id = request.customer_id
        self.timer(self.time_idx) # receiving Puzzle and Solution
        PuzSol = request.puzsol
        customer_id = request.customer_id
        if customer_id in self.customers_lists and len(self.customers_lists[customer_id]) % 4 == 3:
            self.customers_lists[customer_id].append(PuzSol)
        self.executor.submit(self.show_time_list)
        #self.show_time_list()
        #sys.stdout.flush()
        #self.time_idx += 1
        return offchaincommun_pb2.Empty()
    
    def BatchWithdrawC2M(self, request, context):
        with NamedTimerInstance("Merchant handles Customer request in Withdrawal"):
            customer_id = request.customer_id
            signature = request.signature
            blind_sn = request.blind_sn
            Y = request.Y_sgn
            self.executor.submit(self.handle_withdraw_request, signature, blind_sn, Y)
        return offchaincommun_pb2.Empty()

    
def merchant_spend(leader_ip, port, listenport, merchant_id, vk, sk):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    processpool = Pool(4)
    offchaincommun_pb2_grpc.add_OffchainCommunServicer_to_server(MerchantServicer(leader_ip, port, merchant_id, vk, sk, processpool), server)
    print('Merchant listening on port', listenport)
    sys.stdout = Logger_OffchainCommun("merchant")
    server.add_insecure_port('[::]:'+listenport)
    server.start()
    server.wait_for_termination()


def merchant_single_withdrawal(leader_ip, port, merchant_id, sk):
    sys.stdout = Logger_OffchainCommun("merchant")
    num_coin = 1
    merchant = MerchantWithdrawal(leader_ip, port, merchant_id, num_coin, sk)
    merchant.single_blind_sign()


def merchant_batch_withdrawal(leader_ip, port, listenport, merchant_id, vk, sk):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    offchaincommun_pb2_grpc.add_OffchainCommunServicer_to_server(MerchantServicer(leader_ip, port, merchant_id, vk, sk), server)
    print('Merchant%d listening on port %s' % (merchant_id, listenport))
    sys.stdout = Logger_OffchainCommun("merchant")
    server.add_insecure_port('[::]:'+listenport)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    leader_ip, port, listenport, merchant_id, test = merchant_argparser_distributed()
    init_solidity()
    get_contract()
    random.seed(10)
    merchant_sk, vk = merchant_setup()
    #print(vk)
    random.seed()
    if test == "payment":
        merchant_spend(leader_ip, port, listenport, merchant_id, vk, merchant_sk[merchant_id])
    elif test == "withdrawal":
        #merchant_single_withdrawal(leader_ip, port, merchant_id, merchant_sk[merchant_id])
        merchant_batch_withdrawal(leader_ip, port, listenport, merchant_id, vk, merchant_sk[merchant_id])
