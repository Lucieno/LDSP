## Platform
The experiments are running on Ubuntu 18.04 using Google Compute Engine.   

## How to build
The environment of ZeroSnappy has been set in zerosnappy234@gmail.com. Just check the password in Dropbox and run it, or follow the steps to set up the environment.


### Port setting
Follow the instruction in https://docs.bitnami.com/google/faq/administration/use-firewall/ to open tcp port 5000, 8080, and 8545. 

### Install Anaconda3 and set up Jupyter notebook
Download the installation package of Anaconda3 and install it:

```
wget http://repo.continuum.io/archive/Anaconda3-4.0.0-Linux-x86_64.sh   
bash Anaconda3-4.0.0-Linux-x86_64.sh
```

Allow the installer to prepend the installed location to PATH:
```
Do you wish the installer to prepend the 
Anaconda3 install location to PATH 
in your /home/zerosnappy234/.bashrc ? 
[yes|no][no] >>> yes
```

Source the bashrc:
```
source ~/.bashrc
```

Create the configuration file for Jupyter notebook:
```
jupyter notebook --generate-config
```

Append the following lines in ~/.jupyter/jupyter_notebook_config.py:
```
c = get_config()
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.port = 5000
``` 



### Package installation
Create and activate the virtual environment of python3.6.5:
```
conda create -n py3.6 python=3.6.5
source activate py3.6
```

Install the required packages:
```
pip install --user ipykernel, onetimepad, py_ecc, sha3, pysha3, web3, sympy
```

Add the py3.6 as ipython kernal:
```
python -m ipykernel install --user --name=py3.6
```

Install nodejs, truffle and ganache-cli:
```
sudo apt install npm
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
sudo apt install nodejs
sudo npm install -g truffle
sudo npm install -g ganache-cli
```

Follow the steps in https://github.com/Lucieno/py_eth_pairing to install the package.

### How to run

Start Ganache-client with 800000000 as maximum amount of gas and 40 accounts
```
ganache-cli -l 800000000 -a 40 --allowUnlimitedContractSize
```


Use Truffle to deploy the contract to Ganache-cli, and copy the contract address and paste it in the notebook later
```
cd zerosnappy/solidity-bls-test
truffle migrate
```

Start jupyter notebook
```
jupyter-notebook --no-browser --port=5000
```

Open partially-blinded-signature-py-eth-ecc.ipynb and select py3.6 as kernal, then paste the address of the contract copied just now on contract_address


## Gas usage

Get number of funded coins: 22144  
Get number of coins not being verified: 22165  
Merchant registers by submitted pk in G1 and G2: 198728  
Fund 1 coin using a puzzle: 165085  
Submit epsilon_prime of a coin with ID: 87615  
Verify a target coin with ID: 147025  
Batch funding 30 coins with 30 puzzles: 3794113  
Verify all 30 unverified coins: 4117515  
Verifying a Merkle Root with 4 leaves: 25240  
Verifying a Merkle Root with 2<sup>10</sup> leaves: 32428   
Batch funding 2<sup>10</sup> coins by storing the merkle root of puzzles: 114888   
Compute a blind puzzle given the puzzle and r on chain: 127735   


### Gas usage (partially blinded puzzles / maximum batch size as 256 can be support in our framework based on testing) 

1. Submit the sum of public keys of all merchants (submit_pk_sum): 145681   
2. Batch funding with the merkle root of 16 partially blinded puzzles and the merkle roots of the corresponding r (batch_funding_merkle): 195641   
3. Submit the opening of a partially blinded puzzle by giving the blind factor then recompute Y_prime and verify it with the stored merkle root (verify_opening): 78309   
4. Submit the batch of blinded solutions (S_prime) and compute their merkle root on chain (computes_merkle_root_from_X_Y):

| number of blinded solutions | Gas usage |
|:---------------------------:|:---------:|
|              16             |   53318   |
|              32             |   117525  |
|              64             |   196554  |
|             128             |   400100  |
|             256             |   782346  |
   
5. Submit the batch of blinded solutions (S_prime) and compute their merkle root and store it on chain (submit_solution_merkle):

| number of blinded solutions | Gas usage |
|:---------------------------:|:---------:|
|              16             |   83217   |
|              32             |   147712  |
|              64             |   211336  |
|             128             |   406887  |
|             256             |   812533  |
   
6. Customer challenges for a correct solution S on chain (challenge_a_solution): 188933    
7. Customer challenges for a wrong solution S with wrong h (challenge_a_solution): 47461   
8. Customer challenges for a wrong solution S with correct h and a wrong r (challenge_a_solution): 49066   
9. Customer challenges for a wrong solution S with correct h, r and a wrong S (challenge_a_solution): 188955   
10. Customer submits the keys which decrypts different number of coins and the corresponding index of the ciphers, and verify the correctness of the key-cipher-index pair (verify_key_cipher_index_pair2):   

| number of coins | Gas usage |
|:---------------:|:---------:|
|        16       |   34966   |
|        32       |   46184   |
|        64       |   68541   |
|       128       |   113212  |
|       256       |   202666  |

11. Customer submits sigma_sn on chain and verify if it is signed by the leader (verify_leader_signature): 30124    
12. Merchant redempts a coin by submitting batch_id, t, r, alpha, beta, coin_id, merkle proof of Y' and the leader signature (redemption): 151611   
13. Customer withdraws a coin by submitting batch_id, t, r, alpha, beta, coin_id (customer_withdrawal): 142536   
14. Update the balance of each merchant given the batch id (round_consensus): 102028   

### Throughtput(puzzle per second)

1. Customer Off-chain puzzle generate: 2631.57894   
2. Customer Off-chain puzzle blinding: 1388.88888 
3. Consortium (32 merchants, parallelly solving using their pk, and finally aggregating the result together) Off-chain puzzle blind solution: 1724.13793   
4. Customer Off-chain puzzle unblind: 440.52863   
5. Customer Off-chain puzzle verification: 160.00000   
