import os
import sys
import csv

from src_python.config import Config                                                                                
from src_python.session import get_store_path
from src_python.config import ExpConfig

logfile_path = get_store_path(Config.log_file_name, suffix="")
csv_path = logfile_path.strip("log") + "csv"
customer_logfile_path = get_store_path(Config.log_file_name[:-4], suffix="_customer.log")
merchant_logfile_path = get_store_path(Config.log_file_name[:-4], suffix="_merchant.log")
leader_logfile_path = get_store_path(Config.log_file_name[:-4], suffix="_leader.log")

#batch_size = -1
test = "payment"
#test = "withdrawal"
#test ="aggregate"
merchant_log_len = -1

def find_coin_latency_bandwidth(line):
    line = line.split()
    idx = line.index("times") - 1
    time = int(line[idx])

    idx = line.index("coin") - 1
    coin = int(line[idx])

    idx = line.index("latency") + 1
    latency = line[idx]

    idx += 2
    bandwidth = line[idx]

    idx = line.index("merchants") - 1
    num_merchant = int(line[idx])

    batch_size = -1

    if "size" in line:
        idx = line.index("size") + 1
        batch_size = int(line[idx][:-1])

    if test == "withdrawal":
        global customer_log_len, leader_log_len, merchant_log_len
        num_round = coin / batch_size
        print("num round", num_round, "batch size", batch_size, "num_merchant", num_merchant)
        customer_log_len = int(2 + num_round * (2+3) + 3)
        leader_log_len = int(2 + num_round * (7))
        merchant_log_len = int(num_round * (4+1+1) * (num_merchant - 1))
    return time, coin, batch_size, latency, bandwidth, num_merchant

def handle_operation(line):
    operation = line[0][len("Time for "):]
    #print("line", line)
    #print("operation", operation, "line[1]", line[1], "line", line)
    try:
        ms_idx = line[1].index('s')
    except:
        print("line", line)
    time = line[1][1:ms_idx-2]
    time = float(time)
    operations = operation_dict[(num_coin, batch_size, latency, bandwidth, num_merchant)]
    if operation not in operations:
        operations[operation] = [time, 1]
    else:
        operations[operation][0] += time
        operations[operation][1] += 1

def aggregate_figures():
    for line in sys.stdin:
        line = line.strip()
        line = line.split()
        folder = line[1]
        os.system('cat running_data/%s/logfile.csv >> running_data/logfile.csv' % folder)
        os.system('cat running_data/%s/logfile_summary.csv >> running_data/logfile_summary.csv' % folder)

if __name__ == "__main__":
    operation_dict = {}
    latency = -1
    bandwidth = -1
    num_coin = -1
    num_merchant = -1
    batch_size = -1
    operation_dict[(num_coin, batch_size, latency, bandwidth, num_merchant)] = {}
    idx = -1
    if test=="withdrawal":
        num_round = ExpConfig.num_coin_total // ExpConfig.num_coin_batch
        #print("num round", num_round)
        customer_log_len = 2 + num_round * (2+3) + 3
        leader_log_len = 2 + num_round * (7 +1)
        merchant_log_len = num_round * (4+1) * (num_merchant - 1)
    elif test=="payment":
        customer_log_len = 3
        leader_log_len = 3
        merchant_log_len = 6
    elif test=="aggregate":
        aggregate_figures()
        print("Complete aggregate")
        exit()
    with open(customer_logfile_path, 'r') as f_c, open(merchant_logfile_path, 'r') as f_m, open(leader_logfile_path, 'r') as f_l:
        for line in f_c:
            line = line.split(":")
            if line[0].startswith("="):
                time, num_coin, batch_size, latency, bandwidth, num_merchant = find_coin_latency_bandwidth(line[0])
                if (num_coin, batch_size, latency, bandwidth, num_merchant) not in operation_dict:
                    operation_dict[(num_coin, batch_size, latency, bandwidth, num_merchant)] = {}
                idx = 0
                print("customer_log_len", customer_log_len, "merchant log len", merchant_log_len, "leader_log_len", leader_log_len)
                continue
            elif not line[0].startswith("Time for"):
                #print("LINE ", line[0])
                continue
            if idx % customer_log_len == 0:
                for _ in range(merchant_log_len):
                    line_ = f_m.readline()
                    records = line_.split("Time")
                    for record in records[1:]:
                        line_ = "Time" + record 
                        handle_operation(line_.split(":"))
                for _ in range(leader_log_len):
                    line_ = f_l.readline()
                    records = line_.split("Time")
                    for record in records[1:]:
                        line_ = "Time" + record
                        handle_operation(line_.split(":"))
            idx += 1
            handle_operation(line)

    total_time = 0
    summary_path = csv_path[:-4] + "_summary.csv"
    num_result = 0
    with open(csv_path, 'w') as f_w, open(summary_path, 'w') as f:
        csv_writer = csv.writer(f_w, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        summarycsv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for setting, operation_result in operation_dict.items():
            if not operation_result:
                continue
            num_result += 1
            num_coin, batch_size, latency, bandwidth, num_merchant = setting
            if(batch_size > 0):
                csv_writer.writerow([num_coin, "coin", "Batch size", batch_size, "Latency", latency, "Bandwidth", bandwidth, num_merchant, "merchants"])
                summarycsv_writer.writerow([num_coin, "coin", "Batch size", batch_size, "Latency", latency, "Bandwidth", bandwidth, num_merchant, "merchants"])
            else:
                if(test == "withdrawal"):
                    print("batch size", batch_size)
                csv_writer.writerow([num_coin, "coin", "Latency", latency, "Bandwidth", bandwidth, num_merchant, "merchants"])
                summarycsv_writer.writerow([num_coin, "coin", "Latency", latency, "Bandwidth", bandwidth, num_merchant, "merchants"])
            csv_writer.writerow(["Operation", "Time (ms)"])
            for operation, result in operation_result.items():
                time = result[0] / result[1]
                csv_writer.writerow([operation, time])
                if(test == "withdrawal"):
                    if(operation.startswith("Customer") and "Customer Blinding in Withdrawal" not in operation):
                        total_time += time                    
                elif(test == "payment"):
                    if(operation.startswith("Client")):
                        total_time += time
            csv_writer.writerow(["Total time", total_time])
            summarycsv_writer.writerow(["Total time(ms)", total_time])
            total_time = 0
        print("Number of differene tests =",num_result)
