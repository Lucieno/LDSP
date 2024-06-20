import json

from coin import Coin
from config import ExpConfig


def generate_blinded_coin(num_coin):
    t = ExpConfig.epoch_index

    for i in range(num_coin):
        coin = Coin(t)
        # out = json.dumps(coin.__dict__)
        # recon_coin = json.loads(out, object_hook=Coin)
        # print(hex(recon_coin.sn))


if __name__ == "__main__":
    generate_blinded_coin(ExpConfig.num_coin)
