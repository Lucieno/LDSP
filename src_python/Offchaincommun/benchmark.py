import os                                                                       
from multiprocessing import Pool, Process
from time import sleep
import sys

from src_python.Offchaincommun.utils import benchmark_argparser_distributed, find_latency_bandwidth, print_setting                                                                                
#from src_python.Offchaincommun.summarize_result import logfile_path, csv_path                                                                                                                 

from src_python.config import ExpConfig


def run_process(process):                                                             
    os.system('python {}'.format(process))                                       


def payment(ip, num_coin, num_test):
    customer_proc = ('-m src_python.Offchaincommun.customer --ip %s --coin %d --num_test %d --test payment' % (ip, num_coin, num_test))
    
    leader_p = Process(target=run_process, args=(('-m src_python.Offchaincommun.leader'), ))
    leader_p.start()
    merchant_p = Process(target=run_process, args=(('-m src_python.Offchaincommun.merchant --ip %s --ID 1 --test payment') % ip, ))
    sleep(5)
    merchant_p.start()
    p = Process(target=run_process, args=(customer_proc, ))
    sleep(5)
    p.start()
    p.join()
    leader_p.terminate()
    merchant_p.terminate()


def withdrawal(ip, num_coin, num_test):    
    leader_p = Process(target=run_process, args=(('-m src_python.Offchaincommun.leader'), ))
    leader_p.start()
    sleep(2)
    customer_proc = ('-m src_python.Offchaincommun.customer --ip %s --coin %d --port 33150 --num_test %d --test withdrawal' % (ip, num_coin, num_test))
    p = Process(target=run_process, args=(customer_proc, ))
    p.start()
    merchant_lst = []
    for i in range(1, ExpConfig.num_merchant):
        merchant_p = Process(target=run_process, args=(('-m src_python.Offchaincommun.merchant --ip %s --ID %d --test withdrawal') % (ip, i), ))
        merchant_p.start()
        merchant_lst.append(merchant_p)
    p.join()
    leader_p.terminate()
    for merchant_p in merchant_lst:
        merchant_p.terminate()

def batch_withdrawal(ip, num_test):    
    leader_p = Process(target=run_process, args=(('-m src_python.Offchaincommun.leader'), ))
    leader_p.start()
    sleep(2)
    merchant_lst = []
    for i in range(1, ExpConfig.num_merchant):
        merchant_p = Process(target=run_process, args=(('-m src_python.Offchaincommun.merchant --ip %s --ID %d --Mport %d --test withdrawal') % (ip, i, 33199+i), ))
        merchant_p.start()
        merchant_lst.append(merchant_p)
    sleep(32)
    customer_proc = ('-m src_python.Offchaincommun.customer --ip %s --port 33150 --num_test %d --test withdrawal' % (ip, num_test))
    p = Process(target=run_process, args=(customer_proc, ))
    p.start()

    p.join()
    leader_p.terminate()
    for merchant_p in merchant_lst:
        merchant_p.terminate()

if __name__ == "__main__":
    ip, num_coin, num_test, test = benchmark_argparser_distributed()
    print_setting(num_coin, num_test, test)
    if test == "payment":
        payment(ip, num_coin, num_test)
    elif test == "withdrawal":
        if num_coin > 1:
            batch_withdrawal(ip, num_test)
        else:
            withdrawal(ip, num_coin, num_test)
