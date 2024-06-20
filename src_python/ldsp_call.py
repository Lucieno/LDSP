from web3.auto import w3
import timeit

from src_python.coin import Coin, bls_sign_to_lst
from src_python.config import ExpConfig, Config
from src_python.curve_helper import hash_to_bytes32, get_packed_encoding, g2_to_int_lst
from src_python.encryption import seg_locate
from src_python.merkle import get_merkle_root, get_merkle_proof
from src_python.solidity_helper import get_contract_account
from eth_account.messages import defunct_hash_message, encode_defunct


def flatten_lst(lst):
    return [item for sublist in lst for item in sublist]


def call_transact(func, call_meta, is_call=True, is_transact=True):
    func_name = func.fn_name
    res = None
    if is_call:
        res = func.call(call_meta)
        print("%s result:" % func_name, res)
        # print("whole receipt:", tx_receipt)
    if is_transact:
        tx_hash = func.transact(call_meta)
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print("%s used gas: %d" % (func_name, tx_receipt.gasUsed))
    return res


def set_vk(vk):
    contract, account = get_contract_account()
    return call_transact(contract.functions.setVk(g2_to_int_lst(vk)),
                         {'from': account["leader"]})


def set_epoch_index():
    contract, account = get_contract_account()
    return call_transact(contract.functions.setEpochIndex(ExpConfig.epoch_index),
                         {'from': account["leader"]})


def single_withdraw_fund(fund_id, committed_y, blind_sn):
    contract, account = get_contract_account()
    return call_transact(contract.functions.singleWithdrawFund(fund_id, committed_y, blind_sn),
                         {'from': account["customer"], "value": Config.coin_worth})


def single_withdrawal_blind_sign(fund_id, blind_sign):
    contract, account = get_contract_account()
    return call_transact(contract.functions.singleWithdrawalBlindSign(fund_id, blind_sign),
                         {'from': account["leader"]})


def single_withdrawal_challenge_blind_sign(fund_id, committed_y, blind_sn, blind_sign):
    contract, account = get_contract_account()
    return call_transact(
        contract.functions.singleWithdrawalChallengeBlindSign(
            fund_id, committed_y, blind_sn, blind_sign),
        {'from': account["customer"]})


def check_balance():
    contract, account = get_contract_account()
    balance = w3.eth.get_balance(contract.address)
    print("Contract's balance:", balance)
    return balance


def read_epoch_hash():
    contract, account = get_contract_account()
    return call_transact(
        contract.functions.getEpochHash(),
        {'from': account["customer"]},
        is_transact=False)


def get_encoded(x):
    contract, account = get_contract_account()
    return call_transact(
        contract.functions.getEncoded(x),
        {'from': account["customer"]},
        is_transact=False)


def get_hashed(x):
    contract, account = get_contract_account()
    return call_transact(
        contract.functions.getHashed(x),
        {'from': account["customer"]},
        is_transact=False)


def batch_withdraw_fund(fund_id, num_coin):
    contract, account = get_contract_account()
    return call_transact(contract.functions.batchWithdrawalFund(fund_id, num_coin),
                         {'from': account["customer"], "value": num_coin * Config.coin_worth})


def batch_withdraw_close(fund_id, num_coin):
    contract, account = get_contract_account()
    return call_transact(contract.functions.batchWithdrawalClose(fund_id, num_coin),
                         {'from': account["customer"]})


def ec_sign(addr, message):
    message_hash = hash_to_bytes32(get_packed_encoding(message))
    return w3.eth.sign(addr, data=message_hash)


def ec_offline_sign(web3_sk, message):
    encode_message = encode_defunct(message)
    sign = w3.eth.account.sign_message(encode_message, private_key=web3_sk).signature
    return sign.hex()


def ec_offline_verify(signer_addr, signature, message):
    # start0 = timeit.default_timer()
    encode_message = encode_defunct(message)
    # start = timeit.default_timer()
    addr = w3.eth.account.recover_message(encode_message, signature=signature)
    # duration = (timeit.default_timer() - start)* (10 ** 3)
    # print("***time for encode_defunct", (start-start0)* (10 ** 3), "ms")
    # print("***time for recover_message**", duration, "ms")
    return (signer_addr == addr)


def customer_ec_sign(message):
    _, account = get_contract_account()
    return ec_sign(account["customer"], message)


def leader_ec_sign_coin(coin: Coin, merchant_addr):
    _, account = get_contract_account()
    return ec_sign(account["leader"], [coin.sn] + bls_sign_to_lst(coin.sign) + [merchant_addr])


def customer_ec_sign_withdraw(prev_coin, curr_coin, web3_sk, blind_sn_y_hash, customer_addr):
    # blind_sn_y_hash, _ = get_merkle_root([[blind_sn[i], y[i][0], y[i][1]] for i in range(ExpConfig.num_coin_batch)])
    customer_sign = ec_offline_sign(web3_sk,
                                    get_packed_encoding([customer_addr, prev_coin, curr_coin, blind_sn_y_hash]))
    return customer_sign


def ec_verify_customer_sign_withdraw(prev_coin, curr_coin, signature, blind_sn_y_hash, customer_addr):
    # blind_sn_y_hash, _ = get_merkle_root([[blind_sn[i], y[i][0], y[i][1]] for i in range(ExpConfig.num_coin_batch)])
    verify_result = ec_offline_verify(customer_addr, signature,
                                      get_packed_encoding([customer_addr, prev_coin, curr_coin, blind_sn_y_hash]))
    return verify_result


def get_leader_account():
    _, account = get_contract_account()
    return account["leader"]


def get_customer_account():
    _, account = get_contract_account()
    return account["customer"]


def get_elem_root_proof(idx, lst):
    elem = lst[idx]
    root, hash = get_merkle_root(lst)
    proof = get_merkle_proof(idx, len(lst), saved_hash=hash)
    return elem, root, proof, hash


def to_bytes32(lst):
    def f(x):
        if isinstance(x, int):
            return x.to_bytes(32, 'big')
        return x

    return list(map(f, lst))


def batch_withdraw_submit_blind_sign(
        fund_id, prev_coin, curr_coin, blind_sn, y, num_total_coin, blind_sign):
    contract, account = get_contract_account()

    blind_sn_y_hash, _ = get_merkle_root([[blind_sn[i], y[i][0], y[i][1]] for i in range(curr_coin)])

    blind_sign = flatten_lst(blind_sign)
    customer_addr = account["customer"]
    customer_sign = ec_sign(customer_addr, [customer_addr, prev_coin, curr_coin, blind_sn_y_hash])

    return call_transact(
        contract.functions.batchWithdrawalSubmitBlindSign(
            fund_id, prev_coin, curr_coin,
            blind_sn_y_hash, customer_sign, customer_addr,
            num_total_coin, blind_sign),
        {'from': account["leader"]})


def batch_withdraw_challenge_blind_sign(
        fund_id, prev_coin, curr_coin,
        blind_sn, y, num_total_coin, blind_sign, challenge_idx):
    contract, account = get_contract_account()

    sny, sny_root, sny_proof, _ = get_elem_root_proof(
        challenge_idx,
        [[blind_sn[i], y[i][0], y[i][1]] for i in range(curr_coin)])
    blind_sign, blind_sign_root, blind_sign_proof, _ = get_elem_root_proof(challenge_idx, blind_sign)

    encoded_sny = to_bytes32(sny + [sny_root] + sny_proof)
    encoded_blind_sign = to_bytes32(list(blind_sign) + [blind_sign_root] + blind_sign_proof)

    return call_transact(
        contract.functions.batchWithdrawalChallengeBlindSign(
            fund_id, prev_coin, curr_coin,
            num_total_coin,
            encoded_sny,
            encoded_blind_sign,
            challenge_idx),
        {'from': account["customer"]})


def single_refund_reveal(fund_id, y, blind_sn, alpha, beta, hashed_sn):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.singleRefundReveal(
            fund_id, list(y), blind_sn, alpha, beta, hashed_sn),
        {'from': account["customer"]})


def single_refund_challenge_opening(fund_id, y, blind_sn, alpha, beta, hashed_sn):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.singleRefundChallengeOpening(
            fund_id, list(y), blind_sn,
            alpha, beta, hashed_sn, account["customer"]),
        {'from': account["leader"]})


def single_refund_challenge_spent(
        fund_id, y, blind_sn, alpha, beta, hashed_sn, sn):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.singleRefundChallengeSpent(
            fund_id, y, blind_sn,
            alpha, beta, hashed_sn, account["customer"],
            sn),
        {'from': account["leader"]})


def batch_refund_reveal(fund_id, revealing_key, left_bound, right_bound, num_total_coin):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.batchRefundReveal(
            fund_id, revealing_key, left_bound, right_bound, num_total_coin),
        {'from': account["customer"]})


def batch_refund_challenge_opening(
        fund_id, left_bound, right_bound, num_total_coin,
        challenge_id,
        revealing_key,
        all_enc_coin, commitment,
        key_enc_coin_sign,
        sn=None):
    contract, account = get_contract_account()

    customer_addr = account["customer"]

    num_key = len(revealing_key)
    key_idx, layer_idx = seg_locate(challenge_id, left_bound, right_bound, num_total_coin)
    key, key_root, key_proof, key_hash = get_elem_root_proof(key_idx, revealing_key)

    enc_idx = layer_idx * num_total_coin + challenge_id
    enc_coin, enc_coin_root, enc_coin_proof, _ = get_elem_root_proof(enc_idx, flatten_lst(all_enc_coin))

    cmt, cmt_root, cmt_proof, _ = get_elem_root_proof(challenge_id, commitment)

    encoded_idx = [fund_id, challenge_id, num_total_coin, left_bound, right_bound]
    encoded_key = to_bytes32([key, key_root, num_key] + key_proof)
    encoded_enc = to_bytes32(list(enc_coin) + [enc_coin_root] + enc_coin_proof)

    if sn is None:  # is catching spent bad customer?
        encoded_cmt = to_bytes32([cmt_root] + cmt + cmt_proof)
        encoded_idx += [0]
    else:
        encoded_cmt = to_bytes32([cmt_root])
        encoded_idx += [sn]

    return call_transact(
        contract.functions.batchRefundChallenge(
            encoded_idx,
            customer_addr,
            encoded_key,
            encoded_enc,
            encoded_cmt,
            key_enc_coin_sign
        ),
        {'from': account["leader"]})


def dummy_args(fund_id, revealing_key, left_bound, right_bound, num_total_coin):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.dummyArgs(
            fund_id, revealing_key, left_bound, right_bound, num_total_coin),
        {'from': account["customer"]})


def single_deposit_submit(coin: Coin, leader_sign):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.singleDepositSubmit(
            coin.sn, bls_sign_to_lst(coin.sign), leader_sign),
        {'from': account["merchant"]})


def single_deposit_challenge_sign_sn(coin: Coin, leader_sign):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.singleDepositChallengeSignSn(
            coin.sn, bls_sign_to_lst(coin.sign), account["merchant"]),
        {'from': account["merchant_victim"]})


def single_deposit_challenge_double_spent(coin: Coin, leaderSignVictim):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.singleDepositChallengeDoubleSpent(
            coin.sn, bls_sign_to_lst(coin.sign), account["merchant"], leaderSignVictim),
        {'from': account["merchant_victim"]})


def round_consensus_submit(round_idx, pending_root, joint_sign, balance):
    contract, account = get_contract_account()

    return call_transact(
        contract.functions.roundConsensusSubmit(
            round_idx, pending_root, joint_sign, balance),
        {'from': account["leader"]})

def challenge_double_spend(coin: Coin, leader_sign_1, leader_sign_2, another_addr):
    contract, account = get_contract_account()

    sign_sn = bls_sign_to_lst(coin.sign)

    return call_transact(
        contract.functions.ChallengeDoubleSpend(
            coin.sn, sign_sn,
            another_addr,
            leader_sign_1,
            leader_sign_2),
        {'from': account["merchant"]})
