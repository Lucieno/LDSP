import json

from web3 import Web3
from web3.auto import w3

from src_python.config import SolConfig, Config, ExpConfig
from src_python.borg import GlobalDict
from src_python.session import get_store_path


def init_solidity():
    web3 = Web3(Web3.HTTPProvider(SolConfig.ganache_url, request_kwargs={'timeout': 60}))
    # address = web3.toChecksumAddress(SolConfig.contract_address)

    web3.eth.default_account = web3.eth.accounts[0]
    account = {"default:": web3.eth.default_account,
               "leader": web3.eth.accounts[1],
               "customer": web3.eth.accounts[2],
               "merchant": web3.eth.accounts[3],
               "merchant_victim": web3.eth.accounts[4],
               "merchant_independent": web3.eth.accounts[5],
               }
    GlobalDict().store("account", account)


    # merchant_account = [web3.eth.accounts[i] for i in range(
    #     ExpConfig.merchant_account_offset, ExpConfig.merchant_account_offset + ExpConfig.num_merchant)]
    # GlobalDict().store("merchant_account", merchant_account)

    return account


def deploy_contract(account):
    with open(SolConfig.truffle_path, 'r') as f:
        truffle_file = json.load(f)
    abi = truffle_file['abi']
    bytecode = truffle_file['bytecode']

    pre_contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = pre_contract.constructor().transact({'from': account["leader"],
                                                   'value': ExpConfig.construct_fund})
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

    with open(get_store_path(Config.contract_addr_file_name, suffix=""), 'w') as f:
        f.write(tx_receipt.contractAddress)

    GlobalDict().store("contract", contract)

    return contract


def get_contract():
    with open(get_store_path(Config.contract_addr_file_name, suffix=""), 'r') as f:
        contract_addr = f.read()
    contract_addr = Web3.toChecksumAddress(contract_addr)

    with open(SolConfig.truffle_path, 'r') as f:
        truffle_file = json.load(f)
    abi = truffle_file['abi']

    contract = w3.eth.contract(address=contract_addr, abi=abi)

    GlobalDict().store("contract", contract)

    return contract


def get_contract_account():
    return GlobalDict().get("contract"), GlobalDict().get("account")

# def compile_contract():
#     compile_files([SolConfig.contract_path])
# with open(SolConfig.contract_path, 'r') as f:
#     source = f.read()
# return compile_source(source)
