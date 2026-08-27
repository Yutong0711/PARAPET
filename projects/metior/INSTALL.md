### Installation and Usage Instructions 

The source code is written in Python and requires no special packages. Therefore, there is no special
installation instructions. Only installing common python packages through standard package management systems, such as apt, yum and pip, is required. For information on the file, please check README.md 

#### Operating Systems 

The source code is tested on Debian 9 and Mac OSX 10.15. To run on Windows, please change the path delimiter from "/" to "\\". 

#### Python Environment

Ptyhon 3.7, from the referenced CPython implementation. 

#### Required Python Packages 

Please install the following python packages: 
1. Numpy 
2. recombinator
3. argparse 

#### Usage

To obtain the results, please invoke the main python script with the following format: 

&quot;$ python3 MetiorArtifacts.py -bench Benchmark -plat Platform -vm VMType -perc TargetStatistic -vali Validation -pos StartingPoint&quot;       

For detailed instructions, please refer to INSTALL.pdf .
