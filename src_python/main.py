import sys
import random
from copy import copy
from random import randint

from py_ecc.bn128 import G1
from py_eth_pairing import curve_add, curve_mul

from src_python.bench_helper import CodeTimer
from src_python.coin import MerchantCoin, CustomerCoin, batch_unblind, get_commitment_lst, bls_sign_to_lst
from src_python.config import ExpConfig, Config
from src_python.crypto_helper import multiply_g0, sum_g1
from src_python.curve_helper import hash_to_bytes32, get_packed_encoding, hash_to_int
from src_python.encryption import encrypt_all_customer_coin, select_reveal_key, verify_batch_opening
from src_python.log_helper import Logger
from src_python.mercus import merchant_setup
from src_python.merkle import get_merkle_root
from src_python.solidity_helper import init_solidity, deploy_contract, get_contract, get_contract_account
from src_python.ldsp_call import set_vk, set_epoch_index, single_withdraw_fund, single_withdrawal_blind_sign, \
    single_withdrawal_challenge_blind_sign, check_balance, \
    batch_withdraw_fund, batch_withdraw_submit_blind_sign, batch_withdraw_challenge_blind_sign, \
    single_refund_reveal, single_refund_challenge_opening, single_refund_challenge_spent, customer_ec_sign, \
    batch_refund_challenge_opening, batch_refund_reveal, flatten_lst, single_deposit_submit, \
    single_deposit_challenge_sign_sn, single_deposit_challenge_double_spent, leader_ec_sign_coin, \
    round_consensus_submit, batch_withdraw_close, challenge_double_spend


def setup_contract():
    print()
    print("Setting up Contract")

    with CodeTimer("Setup Solidity"):
        account = init_solidity()
        contract = deploy_contract(account)
    with CodeTimer("Setup Keys"):
        merchant_sk, vk = merchant_setup()
    with CodeTimer("[ONCHAIN] Set VK"):
        set_vk(vk)
    with CodeTimer("[ONCHAIN] Set Epoch"):
        set_epoch_index()


def single_withdrawal_onchain(is_good_merchant=True):
    print()
    print("Testing for On-chain Single Withdrawal with %s Merchant" % ("Good" if is_good_merchant else "Bad"))

    with CodeTimer("Setup Solidity"):
        init_solidity()
        get_contract()

    with CodeTimer("Acquire Keys"):
        merchant_sk, vk = merchant_setup()

    check_balance()

    with CodeTimer("Withdrawal Merchant Prepare"):
        merchant_coin = MerchantCoin(ExpConfig.epoch_index)
    with CodeTimer("Withdrawal Customer Blinding"):
        customer_coin = CustomerCoin(ExpConfig.epoch_index, merchant_coin.Y)
    with CodeTimer("[ONCHAIN] Withdrawal Customer Fund"):
        fund_id = randint(1, Config.fund_id_max)
        single_withdraw_fund(fund_id, merchant_coin.Y, customer_coin.blinded_message)

    with CodeTimer("Withdrawal Merchant Signing"):
        blinded_coin = merchant_coin.blind_sign_merge(customer_coin.blinded_message, merchant_sk)

    if is_good_merchant is False:
        blinded_coin = curve_add(blinded_coin, G1)

    with CodeTimer("[ONCHAIN] Withdrawal Merchant Sign Submission"):
        single_withdrawal_blind_sign(fund_id, blinded_coin)

    if is_good_merchant:
        with CodeTimer("Withdrawal Customer Unblinding"):
            coin = customer_coin.unblind(blinded_coin, vk)

    check_balance()

    with CodeTimer("[ONCHAIN] Withdrawal Customer Challenge"):
        challenge_res = single_withdrawal_challenge_blind_sign(
            fund_id, merchant_coin.Y, customer_coin.blinded_message, blinded_coin)
    assert (challenge_res is not is_good_merchant)

    check_balance()

    if is_good_merchant:
        with CodeTimer("LDSP coin verification"):
            print("coin verification result:", coin.verify(vk))
        return coin


def batch_withdrawal_onchain(is_good_merchant=True, is_no_challenge=False):
    print()
    print("Testing for On-chain Batch Withdrawal with %s Merchant" % ("Good" if is_good_merchant else "Bad"))

    with CodeTimer("Setup Solidity"):
        init_solidity()
        get_contract()

    with CodeTimer("Acquire Keys"):
        merchant_sk, vk = merchant_setup()

    check_balance()

    with CodeTimer("Withdrawal Merchant Prepare"):
        merchant_coin = [MerchantCoin(ExpConfig.epoch_index) for _ in range(ExpConfig.num_coin_total)]
    with CodeTimer("Withdrawal Customer Blinding"):
        customer_coin = [CustomerCoin(ExpConfig.epoch_index, merchant_coin[i].Y) for i in
                         range(ExpConfig.num_coin_total)]
    with CodeTimer("[ONCHAIN] Withdrawal Customer Fund"):
        fund_id = randint(1, Config.fund_id_max)
        batch_withdraw_fund(fund_id, ExpConfig.num_coin_total)

    num_round = ExpConfig.num_coin_total // ExpConfig.num_coin_batch

    with CodeTimer("Normal Signing and Unblind (0 to round-2)"):
        for round_idx in range(num_round - 1):
            offset = round_idx * ExpConfig.num_coin_batch
            blinded_coin = [
                merchant_coin[offset + i].blind_sign_merge(
                    customer_coin[offset + i].blinded_message, merchant_sk)
                for i in range(ExpConfig.num_coin_batch)]

            batch_unblind(customer_coin[offset:offset + ExpConfig.num_coin_batch], blinded_coin, vk)

    with CodeTimer("Withdrawal Merchant Signing, last round"):
        offset = (num_round - 1) * ExpConfig.num_coin_batch
        blinded_message = [customer_coin[offset + i].blinded_message
                           for i in range(ExpConfig.num_coin_batch)]
        committed_y = [customer_coin[offset + i].Y
                       for i in range(ExpConfig.num_coin_batch)]
        blinded_coin = [
            merchant_coin[offset + i].blind_sign_merge(customer_coin[offset + i].blinded_message, merchant_sk)
            for i in range(ExpConfig.num_coin_batch)]

    if is_good_merchant and is_no_challenge:
        with CodeTimer("[ONCHAIN] Withdrawal Customer Challenge"):
            assert (batch_withdraw_close(fund_id, ExpConfig.num_coin_total))
        return

    challenge_idx = 2
    if is_good_merchant is False:
        blinded_coin[challenge_idx] = curve_add(blinded_coin[challenge_idx], G1)

    with CodeTimer("[ONCHAIN] Withdrawal Merchant Sign Submission, last round"):
        prev_coin = offset
        curr_coin = ExpConfig.num_coin_batch

        batch_withdraw_submit_blind_sign(
            fund_id, prev_coin, curr_coin,
            blinded_message,
            committed_y,
            ExpConfig.num_coin_total,
            blinded_coin)

    check_balance()
    with CodeTimer("[ONCHAIN] Withdrawal Customer Challenge"):
        challenge_res = batch_withdraw_challenge_blind_sign(
            fund_id, prev_coin, curr_coin, blinded_message, committed_y,
            ExpConfig.num_coin_total, blinded_coin, challenge_idx)
        assert (challenge_res is not is_good_merchant)
    check_balance()


def single_refund_onchain(is_good_customer=True, challenge_event="opening"):
    assert (challenge_event in ["opening", "spent"])
    print()
    print("Testing for On-chain Batch Refund for %s Customer and Challenge %s" %
          ("Good" if is_good_customer else "Bad", challenge_event))

    init_solidity()
    get_contract()
    merchant_sk, vk = merchant_setup()

    merchant_coin = MerchantCoin(ExpConfig.epoch_index)
    customer_coin = CustomerCoin(ExpConfig.epoch_index, merchant_coin.Y)
    fund_id = randint(1, Config.fund_id_max)
    single_withdraw_fund(fund_id, merchant_coin.Y, customer_coin.blinded_message)
    blinded_coin = merchant_coin.blind_sign_merge(customer_coin.blinded_message, merchant_sk)
    coin = customer_coin.unblind(blinded_coin, vk)

    check_balance()

    if challenge_event == "opening" and is_good_customer is False:
        alpha = 4
    else:
        alpha = customer_coin.alpha

    with CodeTimer("[ONCHAIN] Refund Customer Reveal"):
        # if the customer is good, it reveals the right alpha
        single_refund_reveal(
            fund_id, merchant_coin.Y, customer_coin.blinded_message,
            alpha, customer_coin.beta, customer_coin.hashed_sn)

    if challenge_event == "opening":
        with CodeTimer("[ONCHAIN] Refund Customer Challenge Reveal"):
            challenge_res = single_refund_challenge_opening(
                fund_id, merchant_coin.Y, customer_coin.blinded_message,
                alpha, customer_coin.beta, customer_coin.hashed_sn)
            assert (challenge_res is not is_good_customer)

    if challenge_event == "spent":
        with CodeTimer("[ONCHAIN] Refund Customer Challenge Spent Coin"):
            # if the customer is good, no merchant can know the sn
            sn = 2 if is_good_customer else customer_coin.sn
            challenge_res = single_refund_challenge_spent(
                fund_id, merchant_coin.Y, customer_coin.blinded_message,
                alpha, customer_coin.beta, customer_coin.hashed_sn,
                sn)

            assert (challenge_res is not is_good_customer)

    check_balance()


def batch_refund_onchain(is_good_customer=True, mode="opening"):
    print()
    print("Testing for On-chain Batch Refund with %s Customer for %s" %
          (("Good" if is_good_customer else "Bad"), mode))

    init_solidity()
    get_contract()
    merchant_sk, vk = merchant_setup()

    num_total_coin = ExpConfig.num_coin_total
    num_batch_coin = ExpConfig.num_coin_batch
    merchant_coin = [MerchantCoin(ExpConfig.epoch_index) for _ in range(ExpConfig.num_coin_total)]
    customer_coin = [CustomerCoin(ExpConfig.epoch_index, merchant_coin[i].Y) for i in
                     range(num_total_coin)]
    fund_id = randint(1, Config.fund_id_max)
    batch_withdraw_fund(fund_id, num_total_coin)

    with CodeTimer("Generate and Sign Enc Coin and Key with Root"):
        all_reveal_key, all_enc_coin = encrypt_all_customer_coin(customer_coin)
        cmt = get_commitment_lst(customer_coin)
        all_enc_coin_root, _ = get_merkle_root(flatten_lst(all_enc_coin))
        cmt_root, _ = get_merkle_root(cmt)
        key_enc_coin_sign = customer_ec_sign([
            fund_id, num_total_coin, all_enc_coin_root, cmt_root])

    num_round = num_total_coin // num_batch_coin
    for round_idx in range(num_round):
        offset = round_idx * num_batch_coin
        blinded_coin = [
            merchant_coin[offset + i].blind_sign_merge(
                customer_coin[offset + i].blinded_message, merchant_sk)
            for i in range(num_batch_coin)]

        batch_unblind(customer_coin[offset:offset + num_batch_coin], blinded_coin, vk)

    check_balance()

    left_bound, right_bound = ExpConfig.reveal_left, ExpConfig.reveal_right
    with CodeTimer("Refund Customer Reveal"):
        revealing_key = select_reveal_key(all_reveal_key, num_total_coin, left_bound, right_bound)

    if is_good_customer is False and mode == "opening":
        revealing_key = [x + 100 for x in revealing_key]

    challenge_id = random.randint(left_bound, right_bound)
    with CodeTimer("[ONCHAIN] Refund Customer Reveal"):
        batch_refund_reveal(fund_id, revealing_key, left_bound, right_bound, num_total_coin)

    with CodeTimer("Refund Merchant Check Key and Opening"):
        wrong_idx = sorted(verify_batch_opening(
            cmt, flatten_lst(all_enc_coin), revealing_key, left_bound, right_bound, num_total_coin))
        print("Number of Wrong Opening:", len(wrong_idx))
        if len(wrong_idx) > 0:
            challenge_id = random.choice(wrong_idx)

    if mode == "spent":
        if is_good_customer is False:
            sn = customer_coin[challenge_id].sn
        else:
            sn = 1234
    else:
        sn = None

    with CodeTimer("[ONCHAIN] Reveal Merchant Challenge"):
        challenge_res = batch_refund_challenge_opening(
            fund_id, left_bound, right_bound, num_total_coin,
            challenge_id,
            revealing_key, all_enc_coin,
            cmt, key_enc_coin_sign,
            sn=sn)
        assert (challenge_res is not is_good_customer)

    check_balance()


def single_deposit_onchain(is_good_leader=True, mode="double_spent"):
    assert (mode in ["double_spent", "sn_signature"])
    print()
    print("Testing for On-chain Single Deposit for %s Leader and Challenge %s" %
          ("Good" if is_good_leader else "Bad", mode))

    init_solidity()
    get_contract()
    merchant_sk, vk = merchant_setup()

    def generate_coin():
        merchant_coin = MerchantCoin(ExpConfig.epoch_index)
        customer_coin = CustomerCoin(ExpConfig.epoch_index, merchant_coin.Y)
        blinded_coin = merchant_coin.blind_sign_merge(customer_coin.blinded_message, merchant_sk)
        return customer_coin.unblind(blinded_coin, vk)

    coin = generate_coin()
    if mode == "sn_signature" and is_good_leader is False:
        dummy_coin = generate_coin()
        coin.sign = copy(dummy_coin.sign)

    with CodeTimer("Deposit Leader Approve"):
        _, account = get_contract_account()
        leaderSign = leader_ec_sign_coin(coin, account["merchant"])

    with CodeTimer("[ONCHAIN] Deposit First Merchant Submit"):
        single_deposit_submit(coin, leaderSign)

    if mode == "sn_signature":
        with CodeTimer("[ONCHAIN] Deposit Independent Merchant Wrong Sign"):
            challenge_res = single_deposit_challenge_sign_sn(coin, leaderSign)
            assert (challenge_res is not is_good_leader)

    if mode == "double_spent":
        if is_good_leader is False:
            leaderSignVictim = leader_ec_sign_coin(coin, account["merchant_victim"])
        else:
            leaderSignVictim = leaderSign
        with CodeTimer("[ONCHAIN] Deposit Victim Merchant Double Spending"):
            challenge_res = single_deposit_challenge_double_spent(coin, leaderSignVictim)
            assert (challenge_res is not is_good_leader)


def round_consensus_onchain(is_good_leader=True, mode="double_spent"):
    assert (mode in ["double_spent", "signature"])
    print()
    print("Testing for On-chain Round Consensus for %s Leader and Challenge %s" %
          ("Good" if is_good_leader else "Bad", mode))

    init_solidity()
    get_contract()
    merchant_sk, vk = merchant_setup()
    num_merhcant = ExpConfig.num_merchant

    num_total_coin = ExpConfig.num_coin_total
    num_batch_coin = ExpConfig.num_coin_batch
    merchant_coin = [MerchantCoin(ExpConfig.epoch_index) for _ in range(ExpConfig.num_coin_total)]
    customer_coin = [CustomerCoin(ExpConfig.epoch_index, merchant_coin[i].Y) for i in
                     range(num_total_coin)]
    fund_id = randint(1, Config.fund_id_max)
    batch_withdraw_fund(fund_id, num_total_coin)

    num_round = num_total_coin // num_batch_coin
    all_coin = []
    for round_idx in range(num_round):
        offset = round_idx * num_batch_coin
        blinded_coin = [merchant_coin[offset + i].blind_sign_merge(
            customer_coin[offset + i].blinded_message, merchant_sk)
            for i in range(num_batch_coin)]

        all_coin += batch_unblind(customer_coin[offset:offset + num_batch_coin], blinded_coin, vk)

    check_balance()

    num_spent_coin = ExpConfig.num_spent_coin
    _, account = get_contract_account()

    # with CodeTimer("Round Consensus Leader Approve Spending"):
    #     leader_spent_sign = [leader_ec_sign_coin(all_coin[i], account["merchant"]) for i in range(num_spent_coin)]

    def hash_spending(coin, merchant_addr):
        return hash_to_bytes32([coin.sn] + bls_sign_to_lst(coin.sign) + [merchant_addr])

    with CodeTimer("Round Consensus Merchants Signing"):
        round_idx = ExpConfig.round_idx
        all_spent_hash = [hash_spending(all_coin[i], account["merchant"]) for i in range(num_spent_coin)]
        pending_root, pending_hash = get_merkle_root(all_spent_hash)
        balance = [0 for _ in range(num_merhcant)]
        balance[0] += num_spent_coin
        balance_hash = hash_to_bytes32(balance)

        msg_to_sign = hash_to_bytes32([round_idx, pending_root, balance_hash])
        msg_to_sign = curve_mul(G1, int.from_bytes(msg_to_sign, 'big'))
        S = [curve_mul(msg_to_sign, sk) for sk in merchant_sk]
        if is_good_leader is False:
            S = S[:-1]
        joint_sign = sum_g1(S)

    with CodeTimer("[ONCHAIN] Round Consensus Leader Submit"):
        submit_res = round_consensus_submit(round_idx, pending_root, joint_sign, balance)
        assert (submit_res == is_good_leader)

    # with CodeTimer("[ONCHAIN] Round Consensus Victim Merchant Challenge Double Spent"):
    #     _, account = get_contract_account()
    #     challenge_idx = 0
    #     coin = all_coin[challenge_idx]
    #     leader_sign_victim = leader_ec_sign_coin(coin, account["merchant_victim"])
    #     challenge_res = round_consensus_challenge_double_spent(
    #         round_idx, pending_root, balance, coin)


def double_spend(is_good_leader=True):
    protocol_name = "DoubleSpendChallenge"
    leader_role = "Good" if is_good_leader else "Bad"
    print(f"\nTesting for {protocol_name} for {leader_role} Leader")

    init_solidity()
    get_contract()
    merchant_sk, vk = merchant_setup()

    def generate_coin():
        merchant_coin = MerchantCoin(ExpConfig.epoch_index)
        customer_coin = CustomerCoin(ExpConfig.epoch_index, merchant_coin.Y)
        blinded_coin = merchant_coin.blind_sign_merge(customer_coin.blinded_message, merchant_sk)
        return customer_coin.unblind(blinded_coin, vk)

    coin = generate_coin()
    coin_another = generate_coin() if is_good_leader else copy(coin)

    _, account = get_contract_account()
    another_addr = account["merchant_victim"]
    leader_sign_1 = leader_ec_sign_coin(coin, account["merchant"])
    leader_sign_2 = leader_ec_sign_coin(coin_another, another_addr)

    check_balance()

    with CodeTimer(f"[ONCHAIN] {protocol_name} Victim Merchant Double Spending"):
        challenge_res = challenge_double_spend(coin, leader_sign_1, leader_sign_2, another_addr)
        assert (challenge_res is not is_good_leader)

    check_balance()


if __name__ == "__main__":
    sys.stdout = Logger()

    setup_contract()
    # print(Config.__dict__)
    # print(ExpConfig.__dict__)
    #
    # single_withdrawal_onchain(is_good_merchant=True)
    # single_withdrawal_onchain(is_good_merchant=False)
    #
    # batch_withdrawal_onchain(is_good_merchant=True, is_no_challenge=True)
    # batch_withdrawal_onchain(is_good_merchant=True, is_no_challenge=False)
    # batch_withdrawal_onchain(is_good_merchant=False)
    #
    # single_refund_onchain(is_good_customer=True, challenge_event="spent")
    # single_refund_onchain(is_good_customer=False, challenge_event="spent")
    # single_refund_onchain(is_good_customer=True, challenge_event="opening")
    # single_refund_onchain(is_good_customer=False, challenge_event="opening")
    #
    # batch_refund_onchain(is_good_customer=True, mode="opening")
    # batch_refund_onchain(is_good_customer=False, mode="opening")
    # batch_refund_onchain(is_good_customer=True, mode="spent")
    # batch_refund_onchain(is_good_customer=False, mode="spent")
    #
    # single_deposit_onchain(is_good_leader=True, mode="sn_signature")
    # single_deposit_onchain(is_good_leader=False, mode="sn_signature")
    # single_deposit_onchain(is_good_leader=True, mode="double_spent")
    # single_deposit_onchain(is_good_leader=False, mode="double_spent")
    #
    # round_consensus_onchain(is_good_leader=False, mode="signature")
    # round_consensus_onchain(is_good_leader=True, mode="signature")

    double_spend(is_good_leader=True)
    double_spend(is_good_leader=False)

    # customer_ec_sign(1)
