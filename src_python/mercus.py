from src_python.bench_helper import CodeTimer
from src_python.config import ExpConfig
from src_python.merchant import load_or_gen_merchant_key
from src_python.coin import CustomerCoin, MerchantCoin, batch_coin_verify, batch_unblind


def merchant_setup():
    merchant_key, merchant_merged_key = load_or_gen_merchant_key(ExpConfig.num_merchant)
    vk = merchant_merged_key.get_vk()
    merchant_sk = [x.sk for x in merchant_key]
    return merchant_sk, vk


def coin_withdrawal(merchant_sk, vk):
    with CodeTimer("Withdrawal Merchant prepare"):
        merchant_coin = [MerchantCoin(ExpConfig.epoch_index) for _ in range(ExpConfig.num_coin)]
    with CodeTimer("Withdrawal Customer Blinding"):
        customer_coin = [CustomerCoin(ExpConfig.epoch_index, merchant_coin[i].Y) for i in range(ExpConfig.num_coin)]
    with CodeTimer("Withdrawal Merchant Signing"):
        blinded_coin = [merchant_coin[i].blind_sign_merge(customer_coin[i].blinded_message, merchant_sk)
                        for i in range(ExpConfig.num_coin)]

    with CodeTimer("Withdrawal Customer Unblinding"):
        coin = batch_unblind(customer_coin, blinded_coin, vk)

    with CodeTimer("LDSP coin verification"):
        assert (batch_coin_verify(coin, vk))
        print("Pass the verification of %d LDSP coins" % len(coin))

    return coin


def test_basic_withdrawal():
    with CodeTimer("Setup"):
        merchant_sk, vk = merchant_setup()

    with CodeTimer("Coin Withdrawal"):
        coin = coin_withdrawal(merchant_sk, vk)


if __name__ == "__main__":
    test_basic_withdrawal()
