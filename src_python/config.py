class Config(object):
    curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
    random_exp_order = 2 ** 20
    sn_order = 2 ** 128
    fund_id_max = 2 ** 128
    coin_worth = 1000
    seg_key_max = 2 ** 254

    running_data_path = "./running_data"
    cur_sid_file_name = "current_session.txt"
    contract_addr_file_name = "contract_addr.txt"
    log_file_name = "logfile.log"
    sid_max = 2 ** 128


class ExpConfig(object):
    epoch_index = 4232
    customer_id = 35
    round_idx = 10
    num_merchant = 32
    # merchant_account_offset = 3
    super_majority = 17
    merchant_id = 21
    num_customer = 4
    num_coin = 2 ** 11
    num_coin_total = 2 ** 12
    num_coin_batch = 2 ** 5
    num_spent_coin = 2 ** 9
    force_merchant_key_generation = False
    construct_fund = 1000000
    reveal_left = 1
    reveal_right = num_coin_total - 3


class SolConfig(object):
    truffle_path = './src_solidity/build/contracts/LDSP.json'
    contract_path = './src_solidity/contracts/LDSP.sol'
    ganache_url = "http://127.0.0.1:8545"
    # contract_address = "0x23bbAA429327ca58eb9938508432B3BA30676Fc5"
