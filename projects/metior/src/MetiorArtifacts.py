# -*- coding: utf-8 -*-

import numpy as np
import numpy.random as npr
import math
from recombinator.optimal_block_length import optimal_block_length
import argparse
import warnings

import load_data

warnings.filterwarnings("ignore")


#Generate moving window blocks for block_bootstrap
def gen_mvwin_blocks(data, block_length):
    #the samples which can generate blocks
    block_count = len(data) - block_length
    blocks = []
    
    for i in range(block_count):
        new_block = data[i : i + block_length]
        blocks.append(new_block)
        
    return np.array(blocks)

#The main logic for bloock bootstrap
def block_bootstrap(data1, data2, bootstrapTimes, percentile, block_length):
    #data1 is the smaller data sample
    #bootstrap times preferred to be larger than 1000
    #percentile could be any integer percentile value or "average"
    
    #generate blocks
    blocks_1 = gen_mvwin_blocks(data1, block_length)
    blocks_2 = gen_mvwin_blocks(data2, block_length)
    
    #generate block1 information
    block_count_1 = blocks_1.shape[0]
    block_length_1 = blocks_1.shape[1]
    required_blocks_1 = math.floor(block_count_1 / block_length_1)
    
    #generate block2 information
    block_count_2 = blocks_2.shape[0]
    block_length_2 = blocks_2.shape[1]
    required_blocks_2 = math.floor(block_count_2 / block_length_2)

    # Apply bootstrap on data1
    index_1 = []
    for i in range(bootstrapTimes):
        idx1 = npr.choice(block_count_1, size = required_blocks_1,
                          replace = True)
        index_1.append(idx1)
    bootstrapData1 = np.array(blocks_1[index_1])

    # Apply bootstrap on data2  
    index_2 = []
    for i in range(bootstrapTimes):
        idx2 = npr.choice(block_count_2, size = required_blocks_2, 
                          replace = True)
        index_2.append(idx2)
    bootstrapData2 = np.array(blocks_2[index_2])
    
    #calculate the statistics
    if (percentile == "average"):
        #un-block and calculate the means        
        data1MeanStarBar = []
        for i in range(bootstrapTimes):
            lis_cache = []
            for j in range(bootstrapData1.shape[1]):
                lis_cache = np.append(lis_cache, bootstrapData1[i][j])
            data1MeanStarBar.append(lis_cache)
            
        data2MeanStarBar = []
        for i in range(bootstrapTimes):
            lis_cache = []
            for j in range(bootstrapData2.shape[1]):
                lis_cache = np.append(lis_cache, bootstrapData2[i][j])
            data2MeanStarBar.append(lis_cache)
        
        data1MeanStar = np.mean(data1MeanStarBar, axis=1) 
        data2MeanStar = np.mean(data2MeanStarBar, axis=1)
        

        errorRates = []
        for i in range(bootstrapTimes):
            bootstrappedError = np.abs(data1MeanStar[i]-data2MeanStar[i])/data2MeanStar[i]
            errorRates.append(bootstrappedError)
        #generate bootstrapped error rate list    
        errorPercentile = np.percentile(errorRates,95)
        #get mean error rate at 95% CL
        return errorPercentile
        
    else:
        #un-block and calculate the percentiles 
        data1PercentileStarBar = []
        for i in range(bootstrapTimes):
            lis_cache = []
            for j in range(bootstrapData1.shape[1]):
                lis_cache = np.append(lis_cache, bootstrapData1[i][j])
            data1PercentileStarBar.append(lis_cache)
            
        data2PercentileStarBar = []
        for i in range(bootstrapTimes):
            lis_cache = []
            for j in range(bootstrapData2.shape[1]):
                lis_cache = np.append(lis_cache, bootstrapData2[i][j])
            data2PercentileStarBar.append(lis_cache)
        
        data1PercentileStar = np.percentile(data1PercentileStarBar, percentile, axis=1) 
        data2PercentileStar = np.percentile(data2PercentileStarBar, percentile, axis=1)
        
        errorRates = []
        for i in range(bootstrapTimes):
            bootstrappedError = np.abs(data1PercentileStar[i]-data2PercentileStar[i])/data2PercentileStar[i]
            errorRates.append(bootstrappedError)
        #generate bootstrapped error rate list    
        errorPercentile = np.percentile(errorRates,95)
        #get X-percentile error rate at 95% CL
        return errorPercentile
   


#%%
# Metior main logic
def Metior(weeks, percentile, start_point):
    #set which point to start
    print("Starting from point: ", start_point)
    test_data = weeks[0][start_point:]
    #weeks[0] contains three weeks of data
    two_weeks_count = math.floor(len(weeks[0])/3*2)
    #One day data will be used as an interval
    intervalSize = int(two_weeks_count/(2*7))
    two_weeks_loop = math.floor(two_weeks_count/intervalSize - 2)
    samples_per_hour = math.ceil(len(weeks[0])/3/7/24)
    #set the object accuracy
    object_accu = 0.97
    
    #set the lower bound for block size, used for automatic block selection
    block_interval = 6
    block_length_bound = block_interval * samples_per_hour
    
    if (percentile == "mean"):
        for i in range(two_weeks_loop):
            #set the block interval for block bootstrap
            b_star = optimal_block_length(test_data[:intervalSize*(i+1)])
            block_length = math.ceil(b_star[0].b_star_cb)
            if block_length_bound >= block_length:
                block_length = block_length_bound            
            errRate = block_bootstrap(test_data[:intervalSize*(i+1)], 
                         test_data[:intervalSize*(i+2)], 
                         1000, "average", block_length)
            if (errRate <= 1-object_accu):
                meanSize = intervalSize*(i+2)
                meanVal = np.mean(test_data[:meanSize])
                print("The Mean value of the dataset: ", \
                      round(meanVal, 4))
                return meanVal
            elif(errRate > 1 - object_accu and i < (two_weeks_loop - 1)):
                continue
            else:
                meanSize = two_weeks_count
                meanVal = np.mean(test_data[:meanSize])
                print("For average:")
                print("Not able to stable. The Mean value of two weeks' data is", \
                      round(meanVal, 4))
                return meanVal
         

    else:
        percentile = int(percentile)
        for i in range(two_weeks_loop):
            #set the block interval for block bootstrap
            b_star = optimal_block_length(test_data[:intervalSize*(i+1)])
            block_length = math.ceil(b_star[0].b_star_cb)
            if block_length_bound >= block_length:
                block_length = block_length_bound
            errRate = block_bootstrap(test_data[:intervalSize*(i+1)], 
                         test_data[:intervalSize*(i+2)], 
                         1000, percentile, block_length)
            #initial 3 hours vs 6 hours
            if (errRate <= 1-object_accu):
                percSize = intervalSize*(i+2)
                percVal = np.percentile(test_data[:percSize], percentile)
                print("The ", percentile," percentile value of the dataset: ", \
                      round(percVal, 4))
                return percVal
            elif(errRate > 1-object_accu and i < (two_weeks_loop-1)):
                continue
            else:
                percSize = two_weeks_count
                percVal = np.percentile(test_data[:percSize], percentile)
                print("For 90-Tile:")
                print("Not able to stable. " "The ", 
                      percentile,"-ile value of two weeks' data is", \
                          round(percVal, 4))
                return percVal
               


# validate Metior testing results against ground truth
def Metior_validate(weeks, ground_data, percentile, start_point):
    # obtain performance testing results
    perf_result = Metior(weeks, percentile, start_point)
    
    # calculate ground truth
    if (percentile == "mean"):
      ground_truth = np.mean(ground_data)
    else:
      percentile = int(percentile)
      ground_truth = np.percentile(ground_data, percentile)

    # compare performance result vs ground truth
    validate_accu = 1 - np.abs((perf_result - ground_truth) / ground_truth)

    if validate_accu >= 0.965:
        print("Ground truth validation succeed with accuracy: "
              "{0:.2%}".format(validate_accu))
        return True
    else:
        print("Ground truth validation failed with probability: "
              "{0:.2%}".format(validate_accu))
        return False

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#Get order from terminal
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-bench', '--benchmark', help='-bench is used to choose the benchmark',type=str)
parser.add_argument('-vm', '--vm', help='-vm is used to set the VM type',type=str)
parser.add_argument('-plat', '--platform', help='-plat is used to set the platform, aws or chameleon',type=str)
parser.add_argument('-perc', '--percentile', help='-perc is used to set the percentile, mean or any integer from 1 to 99',type=str)
parser.add_argument('-vali', '--validate', help='-vali is used to choose whether to validate with groundtruth',type=str)
parser.add_argument('-pos', '--position', help='-choose which point to set as the initial point',type=int)

args = parser.parse_args()

# load data
data = load_data.load_data(args.benchmark, args.platform, args.vm)

if args.position > len(data["weeks"][0])//3:
  print("-pos out of range, please input integer between 0 and ", len(data["weeks"][0])//3)
  exit(-1)
  print()
else:
  if args.validate == "yes":
    validated = Metior_validate(data["weeks"], data["ground_data"], args.percentile, args.position)
    if not validated:
        print("validation failed")
        exit(-1)
        print()
  else:
    Metior(data["weeks"], args.percentile, args.position)
    print()



