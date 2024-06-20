# OffchainCommun

## How to run at root directory on local computer

Specify the latency and bandwidth in local computer's network:

    sudo tc qdisc replace dev lo root netem delay ${LATENCY}ms rate ${BANDWIDTH}Mbit
  
Start Ganache-client with 800000000 as maximum amount of gas and 40 accounts

    ganache-cli -l 800000000 -a 40 --allowUnlimitedContractSize

On leader's computer:

First, copy leader's private key into leader.py

    python -m src_python.Offchaincommun.leader [--port <port>]
  
On merchants' computers:

    python -m src_python.Offchaincommun.merchant --ip <leader_ip> --test <LDSP operation> [--port <port>] [--ID <MerchantID>] 
   
On customers' computers:

    python -m src_python.Offchaincommun.customer --ip <merchant_ip> --test <LDSP operation> [--port <port>] [--merchantport <port>] [--MID <MerchantID>] [--CID <CustomerID>] [--num_coin <num_coin>]
    
Run leader, merchant, customer with 1 command:

    python -m src_python.Offchaincommun.benchmark --ip <ip> --test <LDSP operation> [--num_test <number of test>] [--coin <number of coin>]
    
Summarize the result at running_data:

    python -m src_python.Offchaincommun.summarize_result

## Explanations
The leader, merchants and clients communicate through socket.

The leader keeps online to receive payment requests from merchants.

The merchant keeps online to receive payment requests from clients.

Once the merchant receives PreSpend from the customer, it forwards PreSpend to the leader.

The leader verifies the request (through leaderSignature.py)

If the request is valid, the leader signs on PreSpend and sends it to the merchant, who then forwards the signature to the customer.

The customer verifies the signature and sends puzzle and solution to the merchant.

The merchant then stores Sign, Puzzle, and Solution in a file called Payment_i, where i represents the transaction number.

## Performance on local virtual machine

### 32 coin
Time for Leader receiving PreSpend to sending Signature: ~34ms

Time for Merchant receiving to sending PreSpend: ~11.5 ms

Time for Merchant sending PreSpend to receiving Signature: ~35 ms

Time for Merchant receiving to sending Signature: ~17 ms

Time for Merchant sending Signature to receiving Puzzle and Solution: ~20 ms

Time for Client generating PreSpend: ~1 ms

Time for Client sending PreSpend to receiving signature: ~70 ms

Time for Client verifying Signature: ~20 ms

Time for Client reading and sending Puzzle and Solution: ~1.5 ms

### 256 coin
Time for Leader receiving PreSpend to sending Signature: ~28ms

Time for Merchant receiving to sending PreSpend: 10.860204696655273 ms

Time for Merchant sending PreSpend to receiving Signature: 27.10437774658203 ms

Time for Merchant receiving to sending Signature: 10.342121124267578 ms

Time for Merchant sending Signature to receiving Puzzle and Solution: 25.18463134765625 ms

Time for Client generating PreSpend: 0.8995532989501953 ms

Time for Client sending PreSpend to receiving signature: 65.60087203979492 ms

Time for Client verifying Signature: 15.540599822998047 ms

Time for Client reading and sending Puzzle and Solution: 1.085042953491211 ms

### 8Mbit bandwidth and 256 num coin
Time for Leader receiving PreSpend to sending Signature: ~20ms

Time for Merchant receiving to sending PreSpend: 19.971609115600586 ms

Time for Merchant sending PreSpend to receiving Signature: 49.689531326293945 ms

Time for Merchant receiving to sending Signature: 12.008428573608398 ms

Time for Merchant sending Signature to receiving Puzzle and Solution: 25.523662567138672 ms

Time for Client generating PreSpend: 0.8852481842041016 ms

Time for Client sending PreSpend to receiving signature: 97.9454517364502 ms

Time for Client verifying Signature: 17.12203025817871 ms

Time for Client reading and sending Puzzle and Solution: 2.853870391845703 ms
