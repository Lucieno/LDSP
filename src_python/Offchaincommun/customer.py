#!/usr/bin/env python3

import os
import random
import secrets
import concurrent
from time import sleep
import timeit

from web3.auto import w3
from eth_account.messages import encode_defunct

import grpc
import src_python.Offchaincommun.offchaincommun_pb2 as offchaincommun_pb2
import src_python.Offchaincommun.offchaincommun_pb2_grpc as offchaincommun_pb2_grpc
from src_python.Offchaincommun.utils import customer_argparser_distributed, NamedTimerInstance, find_latency_bandwidth, print_setting, ec_verify_sign_on_prespend
from src_python.mercus import merchant_setup
from src_python.config import ExpConfig, Config
from src_python.coin import MerchantCoin, CustomerCoin, batch_unblind, get_hash_sn
from src_python.ldsp_call import get_leader_account, single_withdraw_fund, single_withdrawal_blind_sign, \
    single_withdrawal_challenge_blind_sign, batch_withdraw_fund, batch_withdraw_submit_blind_sign, batch_withdraw_challenge_blind_sign, \
    get_customer_account, customer_ec_sign_withdraw
from src_python.merkle import get_merkle_root
from src_python.solidity_helper import init_solidity, get_contract
from src_python.log_helper import Logger_OffchainCommun

import sys

class CustomerCommunBase:
    def __init__(self, leader_ip, port):
        arr = leader_ip + ":" + port
        channel = grpc.insecure_channel(arr)
        self.stub = offchaincommun_pb2_grpc.OffchainCommunStub(channel)
        self.time_dict = dict()
        #self.offset = 0


class CustomerWithdrawalCommun:
    def __init__(self, merchant_ip_lst, port=33200):
        self.merchantstub_lst = []
        self.time_for_blinding = 0
        for merchant_ip in merchant_ip_lst:
            arr = merchant_ip + ":" + str(port)
            channel = grpc.insecure_channel(arr)
            self.merchantstub_lst.append(offchaincommun_pb2_grpc.OffchainCommunStub(channel))
            port += 1            

    def withdrawal_start(self, num_coin):
        with NamedTimerInstance("Customer setting request in Withdrawal"):
            self.blind_coin_lst = []
            self.fund_id = random.randint(1, Config.fund_id_max)
            request = offchaincommun_pb2.WithdrawalRequest(customer_id=self.customer_id, fund_id=str(self.fund_id), num_coin=num_coin)
            self.initialcoinlst = []
        with NamedTimerInstance("Customer sending request in Withdrawal"):
            response_iterator = self.stub.StartWithdrawal(request)
        Y_lst = []
        with NamedTimerInstance("Customer receiving Y and Blinding in Withdrawal"):
            wait_jobs = []
            for response in response_iterator:
                Y = response.Y
                Y = Y.split(';')
                Y_lst.extend(Y)
                #wait_jobs.append(self.executor.submit(self.customer_blinding, Y))
                num_coin -= ExpConfig.num_coin_batch
                if(num_coin == 0):
                    break
            start_time = timeit.default_timer()
            idx = 0
            for Y in Y_lst:
                idx += 1
                self.customer_blinding(Y)
        duration = (timeit.default_timer() - start_time) * (10 ** 3)
            #concurrent.futures.wait(wait_jobs)
        #print("Time for blinding:", self.time_for_blinding * (10 ** 3), "ms")
        print("Time for Customer Blinding in Withdrawal:", duration, "ms")
        self.time_for_blinding = 0

    def withdraw_broadcastsign(self, sign, blind_message, y_lst):
        blind_message_ = ""
        for blind_sn in blind_message:
            blind_message_ += str(blind_sn) + ";"
        blind_message_ = blind_message_.strip(';')
        y_str = ""
        for y in y_lst:
            Y_prime_X, Y_prime_Y = y
            y_str += str(Y_prime_X) + "," + str(Y_prime_Y) + ";"
        y_str = y_str.strip(';')
        request = offchaincommun_pb2.CustomerSign(
            customer_id=self.customer_id, signature=sign, blind_sn=blind_message_, Y_sgn=y_str)
        for merchantstub in self.merchantstub_lst:
            self.executor.submit(merchantstub.BatchWithdrawC2M, request)
            #merchantstub.BatchWithdrawC2M(request)
        response_iterator = self.stub.BatchWithdrawC2L(request)
        for response in response_iterator:
            blind_coin = response.signature
            blind_coin_lst = blind_coin.split(';')
            blind_coin_lst_ = []
            for blind_coin in blind_coin_lst:
                blinded_sgn_X, blinded_sgn_Y = blind_coin.split(',')
                blind_coin_lst_.append((int(blinded_sgn_X), int(blinded_sgn_Y)))

            self.blind_coin_lst.extend(blind_coin_lst_)

class CustomerPaymentCommun:
    def start_payment(self):
        with NamedTimerInstance("Client sending PreSpend to receiving signature"):
            paymentinfo = offchaincommun_pb2.PaymentInfo(customer_id=self.customer_id, prespend=self.prespend)
            response_iterator = self.stub.StartPayment(paymentinfo)
            for response in response_iterator:
                self.signature_lst = response.signature.split()

    def complete_payment(self):
        with NamedTimerInstance("Client reading and sending Solution"):
            data = ""
            for coin in self.pay_coinlst:
                    data += str(coin.sn)
            PuzSol = offchaincommun_pb2.PuzSol(customer_id=self.customer_id, puzsol=data)
            response = self.stub.TransmitPuzSol(PuzSol)


class CustomerPayment(CustomerPaymentCommun):
    def __init__(self, merchant_id):
        self.prespend = ""
        self.signature = ""
        self.prespend_lst = []
        self.signature_lst = []
        self.pay_coinlst = []
        #self.before_payment(merchant_id)
   
    def storeLDSPcoin(self, coin_lst):
        self.pay_coinlst.extend(coin_lst)

    def gen_offchain_coin(self, merchant_sk): # simulate the case that offchain coins are already generated
        merchant_coin = [MerchantCoin(ExpConfig.epoch_index) for _ in range(ExpConfig.num_coin_total)]
        customer_coin = [CustomerCoin(ExpConfig.epoch_index, merchant_coin[i].Y) for i in
                             range(ExpConfig.num_coin_total)]
        num_round = ExpConfig.num_coin_total // ExpConfig.num_coin_batch
        coin_lst_ = []
        for round_idx in range(num_round):
            offset = round_idx * ExpConfig.num_coin_batch
            blinded_coin = [
                merchant_coin[offset + i].blind_sign_merge(
                customer_coin[offset + i].blinded_message, merchant_sk)
                for i in range(ExpConfig.num_coin_batch)]

            coin_lst = batch_unblind(customer_coin[offset:offset + ExpConfig.num_coin_batch], blinded_coin, vk)
            coin_lst_.extend(coin_lst)
        if(self.num_coin > len(coin_lst_)):
            print("Error: The number of coin is larger than the length of coin list")
            raise Exception
        self.pay_coinlst = coin_lst_[:]

    def gen_PreSpend(self, coin):
        S_prime, Y_prime = coin.sign
        S_prime_X, S_prime_Y = S_prime
        Y_prime_X, Y_prime_Y = Y_prime
        hashed_sn = get_hash_sn(coin.sn)

        M_BLS = "%d,%d,%d,%d,%d,%d" % (S_prime_X, S_prime_Y, Y_prime_X, Y_prime_Y, hashed_sn, coin.t)
        return M_BLS

    def before_payment(self, num_coin):
        self.prespend = ""
        self.prespend_lst = []
        self.num_coin = num_coin
        self.pay_coinlst = self.pay_coinlst[:num_coin]
        for coin in self.pay_coinlst:
            prespend = self.gen_PreSpend(coin)
            self.prespend += prespend + " "
            self.prespend_lst.append(prespend)
        self.prespend = self.prespend[:-1]

    def verify_sign(self):
        with NamedTimerInstance("Client verifying Signature"):
            valid_sgn = True
            for sgn, prespend in zip(self.signature_lst, self.prespend_lst):
                verify_result = self.verify_sign_on_prespend(sgn, prespend)
                valid_sgn = (valid_sgn and verify_result)
        return valid_sgn

    def verify_sign_on_prespend(self, signed_prespend, prespend):
        prespend_encode = encode_defunct(text=prespend)
        addr = w3.eth.account.recover_message(prespend_encode, signature=signed_prespend)
        return (addr == self.leader_account)


class CustomerWithdrawal(CustomerWithdrawalCommun):
    def __init__(self):
        merchant_ip_lst = ["127.0.0.1" for i in range(ExpConfig.num_merchant-1)]
        CustomerWithdrawalCommun.__init__(self, merchant_ip_lst)
        self.customer_sign_lst = []
        self.blind_coin_lst = []

    def customer_blinding(self, Y):
        #time_start = timeit.default_timer()
        Y_prime_X, Y_prime_Y = Y.split(',')
        Y_ = (int(Y_prime_X), int(Y_prime_Y))
        customer_coin = CustomerCoin(ExpConfig.epoch_index, Y_)
        self.initialcoinlst.append(customer_coin)
        #self.time_for_blinding += timeit.default_timer() - time_start

    def single_onchain_withdraw_fund(self):
        #fund_id = randint(1, Config.fund_id_max)
        customer_coin = self.initialcoinlst[0]
        single_withdraw_fund(self.fund_id, customer_coin.Y, customer_coin.blinded_message)
        self.upload_blindmsg_Y_to_SC()

    def batch_onchain_withdraw_fund(self):
        batch_withdraw_fund(self.fund_id, ExpConfig.num_coin_total)

    def batch_onchain_withdraw_signing_broadcast(self, prev_coin, curr_coin, round_idx):
        #with NamedTimerInstance("Customer Withdrawal Sign and Broadcast at round %d" % round_idx):
        with NamedTimerInstance("Customer Set sn' and y in Withdrawal at round %d" % round_idx):
            blinded_message = [coin.blinded_message for coin in self.initialcoinlst[prev_coin:curr_coin]]
            committed_y = [coin.Y for coin in self.initialcoinlst[prev_coin:curr_coin]]
        with NamedTimerInstance("Customer Computes MHTRoot in Withdrawal at round %d" % round_idx):
            blind_sn_y_hash, _ = get_merkle_root([[blinded_message[i], committed_y[i][0], committed_y[i][1]] for i in range(ExpConfig.num_coin_batch)])
        with NamedTimerInstance("Customer Signs on Statement in Withdrawal at round %d" % round_idx):
            sign = customer_ec_sign_withdraw(prev_coin, curr_coin, self.web3_sk, blind_sn_y_hash, self.customer_account)
        with NamedTimerInstance("Customer Broadcast Sign and Receive Blind Sign in Withdrawal at round %d" % round_idx):
            self.withdraw_broadcastsign(sign, blinded_message, committed_y)

    def upload_blindmsg_Y_to_SC(self):
        with open(Config.blindmsg_Y_path, 'w') as f:
            for coin in self.initialcoinlst:
                Y_prime_X, Y_prime_Y = coin.Y
                f.write("%d,%d,%d;" %(coin.blinded_message, Y_prime_X, Y_prime_Y))
                #print("Upload Customer blindmsg_Y", coin.blinded_message, Y_prime_X, Y_prime_Y)

    def download_blind_sgn_from_SC(self):
        sleep(1)
        while(not os.path.exists(Config.blind_sgn_path)):
            print(Config.blind_sgn_path, "is not here")
            sleep(1)
        with open(Config.blind_sgn_path, 'r') as f:
            blind_sgns = f.read()
        blind_sgn_lst = blind_sgns.strip(';').split(';')
        blind_sgn_lst_ = []
        for blind_sgn in blind_sgn_lst:
            blinded_sgn_X, blinded_sgn_Y = blind_sgn.split(',')
            blind_sgn_lst_.append((int(blinded_sgn_X), int(blinded_sgn_Y)))
        return blind_sgn_lst_

    def single_unblind_or_challenge(self):
        blind_sgn_lst = self.download_blind_sgn_from_SC()
        blinded_coin = blind_sgn_lst[0]
        customer_coin = self.initialcoinlst[0]
        try:
            with NamedTimerInstance("Customer Unblinding in Withdrawal"):
                coin = customer_coin.unblind(blinded_coin, self.vk)
        except AssertionError: # verify sgn result is False
            #print("Customer Y", customer_coin.Y)
            challenge_res = single_withdrawal_challenge_blind_sign(
            self.fund_id, customer_coin.Y, customer_coin.blinded_message, blinded_coin)
            print("Challenge result:", challenge_res)
        except:
            print("Error in unblinding")
        self.storeLDSPcoin([coin])

    def batch_unblind_or_challenge(self, prev_coin: int, curr_coin: int, num_coin_total: int):
        batch_blinded_coin = self.blind_coin_lst[prev_coin:curr_coin]
        batch_customer_coin = self.initialcoinlst[prev_coin:curr_coin]
        try:
            #with NamedTimerInstance("Customer Unblinding in Withdrawal"):
            coin_lst = batch_unblind(batch_customer_coin, batch_blinded_coin, self.vk)
            self.storeLDSPcoin(coin_lst)
            print("Withdraw succeeds")
        except AssertionError: # verify sgn result is False
            print("Assertion error Customer Y")
            for i, (coin, bld_sign) in enumerate(zip(batch_customer_coin, batch_blinded_coin)):
                S, right = coin.calc_left_right(bld_sign)
                if(coin.verify_blind(S, right, self.vk) is False):
                    print(i, "coin is wrong bld sign:", bld_sign)
            blinded_message = [coin.blinded_message
                for coin in batch_customer_coin]
            committed_Y = [coin.Y 
                for coin in batch_customer_coin]
            challege_idx = self.find_challege_idx()
            challenge_res = batch_withdrawal_challenge_blind_sign(
            self.fund_id, prev_coin, curr_coin, blinded_message, committed_Y, num_coin_total, blinded_coin, challege_idx)
            print("Challenge result:", challenge_res)
        except:
            print("Error in unblinding")
            print("len of blinded_coin", self.blind_coin_lst)

    def find_challege_idx(self):
        raise NotImplementedError


class Customer(CustomerCommunBase, CustomerPayment, CustomerWithdrawal):
    def __init__(self, leader_ip, port, customer_id, merchant_id, num_coin, vk):
        self.customer_id = customer_id
        self.leader_account = get_leader_account()
        self.customer_account = get_customer_account()
        #self.initialcoinlst = []
        self.vk = vk
        self.web3_sk = "0xe9ac8dfbbe4a9a72fc1871fdaf32e161a15af76b9d2fcd5994c32f4b3e08e76d"
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers = 4)
        self.num_coin = num_coin
        CustomerCommunBase.__init__(self, leader_ip, port)
        CustomerPayment.__init__(self, merchant_id)
        CustomerWithdrawal.__init__(self)


def customer_spend(customer, merchant_sk, num_coin, num_test):
    customer.gen_offchain_coin(merchant_sk)
    if num_coin == -1:
        for num in [2048,1024,512,256,128,64,32,16,8,4,2,1]:
            for network in ["delete dev lo root netem delay 20ms rate 100Mbit", "replace dev lo root netem delay 10ms rate 1Gbit", 
                            "replace dev lo root netem delay 20ms rate 100Mbit"]:
                os.system("sudo tc qdisc " + network)
                print_setting(num, num_test, "payment")
                customer.before_payment(num)
                for _ in range(num_test):
                    customer.start_payment()
                    if customer.verify_sign():
                        customer.complete_payment()
                    else:
                        print("Payment leader signature is wrong")
                        exit()
                    sleep(0.5)
    else:
        print_setting(num_coin, num_test, "payment")
        customer.before_payment(num_coin)
        for _ in range(num_test):
            customer.start_payment()
            if customer.verify_sign():
                customer.complete_payment()


def customer_single_withdrawal(customer):
    customer.withdrawal_start(1)
    customer.single_onchain_withdraw_fund()
    customer.single_unblind_or_challenge()


def customer_batch_withdrawal(customer, num_coin, num_test):
    print_setting(num_coin, num_test, "withdrawal")
    for test_no in range(num_test):
        print("+++++++++++++++++++test %d++++++++++++++++++++++" % test_no)
        #with NamedTimerInstance("Customer Start Withdrawal(get Y)"):
        customer.withdrawal_start(ExpConfig.num_coin_total)
        with NamedTimerInstance("Customer Withdrawal Fund"):
            customer.batch_onchain_withdraw_fund()
        num_round = ExpConfig.num_coin_total // ExpConfig.num_coin_batch
        for round_idx in range(num_round):
            offset = round_idx * ExpConfig.num_coin_batch
            curr_coin = offset + ExpConfig.num_coin_batch
            #with NamedTimerInstance("Customer Withdrawal Sign and Broadcast at round %d" % round_idx):
            customer.batch_onchain_withdraw_signing_broadcast(offset, curr_coin, round_idx)
            with NamedTimerInstance("Customer Verify Sign, Unbind and Challenge at round %d" % round_idx):
                customer.batch_unblind_or_challenge(offset, curr_coin, ExpConfig.num_coin_total)
    #print("finish")


if __name__ == "__main__":
    leader_ip, port, merchant_id, customer_id, num_coin, num_test, test = customer_argparser_distributed()
    init_solidity()
    get_contract()

    sys.stdout = Logger_OffchainCommun("customer")
    #print_setting(num_coin, num_test, test)
    random.seed(10)
    merchant_sk, vk = merchant_setup()
    random.seed()
    customer = Customer(leader_ip, port, customer_id, merchant_id, num_coin, vk)

    if test == "payment":
        customer_spend(customer, merchant_sk, num_coin, num_test)
    elif test == "withdrawal":
        #customer_single_withdrawal(customer)
        customer_batch_withdrawal(customer, num_coin, num_test)
