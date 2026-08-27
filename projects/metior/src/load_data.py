#!/usr/bin/python3

import numpy as np

def load_data(bench, platform, vm):
    weeks=[]
    if (bench == "ft") and (platform == "chameleon"):
        if vm == "l":
            # load data for ft.C on CHM large
            HPCLCam = open('./Chameleon/FT-Chameleon/Chameleon-FT-L.txt',"rb")
            HPCLDataCam = np.loadtxt(HPCLCam,
                                     unpack=True,
                                     delimiter=',',
                                     skiprows=0)
            
            FLT1Cam = HPCLDataCam[:2860]
            FLTCam = HPCLDataCam[2860:]
            # sampled 3 weeks
            weeks.append(FLT1Cam)
            # ground truth
            ground_data = FLTCam
        if vm == "m":
            HPCMCam = open('./Chameleon/FT-Chameleon/Chameleon-FT-M.txt',"rb")
            HPCMDataCam = np.loadtxt(HPCMCam,
                                     unpack=True,
                                     delimiter=',',
                                     skiprows=0)

            FMT1Cam = HPCMDataCam[:3423]
            FMTCam = HPCMDataCam[3423:]

            # sampled 3 weeks
            weeks.append(FMT1Cam)
            # ground truth
            ground_data = FMTCam
    
    if (bench == "ep") and (platform == "chameleon"):
        if vm == "l":
            # load data for ep.C on CHM large
            EPL1Cam = open('./Chameleon/EP-Chameleon/Chameleon-EP-L.txt',"rb")
            EPLData1Cam = np.loadtxt(EPL1Cam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            ELT1Cam = EPLData1Cam[:2034]
            ELTCam = EPLData1Cam[2034:]
            # sampled 3 weeks
            weeks.append(ELT1Cam)
            # ground truth
            ground_data = ELTCam

        if vm == "m":
            EPM1Cam = open('./Chameleon/EP-Chameleon/Chameleon-EP-M.txt',"rb")
            EPMData1Cam = np.loadtxt(EPM1Cam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            EMT1Cam = EPMData1Cam[:2155]
            EMTCam = EPMData1Cam[2155:]

            # sampled 3 weeks
            weeks.append(EMT1Cam)
            # ground truth
            ground_data = EMTCam


    if (bench == "ycsb") and (platform == "chameleon"):
        if vm == "m":
            YCSBMCam = open('./Chameleon/YCSB-Chameleon/Chameleon-YCSB-M.txt',"rb")
            YCSBMDataCam = np.loadtxt(YCSBMCam,
                                      unpack=True,
                                      delimiter=',',
                                      skiprows=0)

            YMT1Cam = YCSBMDataCam[:2167]
            YMTCam = YCSBMDataCam[2167:]

            # sampled 3 weeks
            weeks.append(YMT1Cam)
            # ground truth
            ground_data = YMTCam

        if vm == "l":
            #YCSB Load overal runtime
            YCSBLCam = open('./Chameleon/YCSB-Chameleon/Chameleon-YCSB-L.txt',"rb")
            YCSBLDataCam = np.loadtxt(YCSBLCam,
                                      unpack=True,
                                      delimiter=',',
                                      skiprows=0)

            YLT1Cam = YCSBLDataCam[:2008]
            YLTCam = YCSBLDataCam[2008:]

            # sampled 3 weeks
            weeks.append(YLT1Cam)
            # ground truth
            ground_data = YLTCam

        if vm == "s":
            YCSBSCam = open('./Chameleon/YCSB-Chameleon/Chameleon-YCSB-S.txt',"rb")
            YCSBSDataCam = np.loadtxt(YCSBSCam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            YST1Cam = YCSBSDataCam[:1515]
            YSTCam = YCSBSDataCam[1515:]

            # sampled 3 weeks
            weeks.append(YST1Cam)
            # ground truth
            ground_data = YSTCam

    if (bench == "jps") and (platform == "chameleon"):
        if vm == "l":
            JPETLCam = open('./Chameleon/Jpet-Chameleon/Chameleon-JPS-L.txt',"rb")
            JPETLDataCam = np.loadtxt(JPETLCam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            JLT1Cam = JPETLDataCam[:2018]
            JLTCam = JPETLDataCam[2018:]

            # sampled 3 weeks
            weeks.append(JLT1Cam)
            # ground truth
            ground_data = JLTCam

        if vm == "m":
            JPETMCam = open('./Chameleon/Jpet-Chameleon/Chameleon-JPS-M.txt',"rb")
            JPETMDataCam = np.loadtxt(JPETMCam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            JMT1Cam = JPETMDataCam[:2856]
            JMTCam = JPETMDataCam[2856:]

            # sampled 3 weeks
            weeks.append(JMT1Cam)
            # ground truth
            ground_data = JMTCam

        if vm == "s":
            JPETSCam = open('./Chameleon/Jpet-Chameleon/Chameleon-JPS-S.txt',"rb")
            JPETSDataCam = np.loadtxt(JPETSCam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            JST1Cam = JPETSDataCam[:2707]
            JSTCam = JPETSDataCam[2707:]

            # sampled 3 weeks
            weeks.append(JST1Cam)
            # ground truth
            ground_data = JSTCam

    if (bench == "tpcc") and (platform == "chameleon"):
        if vm == "l":
            OLTPL1Cam = open('./Chameleon/TPCC-Chameleon/Chameleon-TPCC-L.txt',"rb")
            OLTPLData1Cam = np.loadtxt(OLTPL1Cam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            OLT1Cam = OLTPLData1Cam[:1686]
            OLTCam = OLTPLData1Cam[1686:]
            # sampled 3 weeks
            weeks.append(OLT1Cam)
            # ground truth
            ground_data = OLTCam

        if vm == "m":
            OLTPM1Cam = open('./Chameleon/TPCC-Chameleon/Chameleon-TPCC-M.txt',"rb")
            OLTPMData1Cam = np.loadtxt(OLTPM1Cam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            OMT1Cam = OLTPMData1Cam[:1922]
            OMTCam = OLTPMData1Cam[1922:]
            # sampled 3 weeks
            weeks.append(OMT1Cam)
            # ground truth
            ground_data = OMTCam

        if vm == "s":
            OLTPS1Cam = open('./Chameleon/TPCC-Chameleon/Chameleon-TPCC-S.txt',"rb")
            OLTPSData1Cam = np.loadtxt(OLTPS1Cam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            OST1Cam = OLTPSData1Cam[:1678]
            OSTCam = OLTPSData1Cam[1678:]
            # sampled 3 weeks
            weeks.append(OST1Cam)
            # ground truth
            ground_data = OSTCam

    if (bench == "ima") and (platform == "chameleon"):
        if vm == "l":
            MEMORYLCam = open('./Chameleon/IMA-Chameleon/Chameleon-IMA-L.txt',"rb")
            MEMORYLDataCam = np.loadtxt(MEMORYLCam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            MLT1Cam = MEMORYLDataCam[:948]
            MLTCam = MEMORYLDataCam[948:]
            # sampled 3 weeks
            weeks.append(MLT1Cam)
            # ground truth
            ground_data = MLTCam

        if vm == "m":
            MEMORYMCam = open('./Chameleon/IMA-Chameleon/Chameleon-IMA-M.txt',"rb")
            MEMORYMDataCam = np.loadtxt(MEMORYMCam,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            MMT1Cam = MEMORYMDataCam[:910]
            MMTCam = MEMORYMDataCam[910:]
            # sampled 3 weeks
            weeks.append(MMT1Cam)
            # ground truth
            ground_data = MMTCam

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #loading data for aws

    if (bench == "ft") and (platform == "aws"):
        if vm == "l":
            # load data for ft.C on AWS large
            HPCLAws = open('./AWS/FT-AWS/AWS-FT-2XL.txt',"rb")
            HPCLDataAws = np.loadtxt(HPCLAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            FLT1Aws = HPCLDataAws[0:2253]
            FLTAws = HPCLDataAws[2253:]
            # sampled 3 weeks
            weeks.append(FLT1Aws)
            # ground truth
            ground_data = FLTAws

        if vm == "m":
            # load data for ft.C on AWS large
            HPCMAws = open('./AWS/FT-AWS/AWS-FT-XL.txt',"rb")
            HPCMDataAws = np.loadtxt(HPCMAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            FMT1Aws = HPCMDataAws[:2285]
            FMTAws = HPCMDataAws[2285:]
            # sampled 3 weeks
            weeks.append(FMT1Aws)
            # ground truth
            ground_data = FMTAws

        if vm == "s":
            # load data for ft.C on AWS large
            HPCSAws = open('./AWS/FT-AWS/AWS-FT-L.txt',"rb")
            HPCSDataAws = np.loadtxt(HPCSAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            FST1Aws = HPCSDataAws[:2032]
            FSTAws = HPCSDataAws[2032:]
            # sampled 3 weeks
            weeks.append(FST1Aws)
            # ground truth
            ground_data = FSTAws

    if (bench == "ep") and (platform == "aws"):
        if vm == "l":
            # load data for ep.C on AWS large
            EPL1Aws = open('./AWS/EP-AWS/AWS-EP-2XL.txt',"rb")
            EPLData1Aws = np.loadtxt(EPL1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            ELT1Aws = EPLData1Aws[:2051]
            ELTAws = EPLData1Aws[2051:]
            # sampled 3 weeks
            weeks.append(ELT1Aws)
            # ground truth
            ground_data = ELTAws

        if vm == "m":
            # load data for ep.C on AWS large
            EPM1Aws = open('./AWS/EP-AWS/AWS-EP-XL.txt',"rb")
            EPMData1Aws = np.loadtxt(EPM1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            EMT1Aws = EPMData1Aws[:2026]
            EMTAws = EPMData1Aws[2026:]
            # sampled 3 weeks
            weeks.append(EMT1Aws)
            # ground truth
            ground_data = EMTAws

        if vm == "s":
            # load data for ep.C on AWS large
            EPS1Aws = open('./AWS/EP-AWS/AWS-EP-L.txt',"rb")
            EPSData1Aws = np.loadtxt(EPS1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            EST1Aws = EPSData1Aws[:2031]
            ESTAws = EPSData1Aws[2031:]
            # sampled 3 weeks
            weeks.append(EST1Aws)
            # ground truth
            ground_data = ESTAws
    
    if (bench == "jps") and (platform == "aws"):
        if vm == "l":
            # load data for jps on AWS 2Xlarge
            #Jpet succesful requests
            JPETL1Aws = open('./AWS/Jpet-AWS/AWS-JPS-2XL.txt',"rb")
            JPETLData1Aws = np.loadtxt(JPETL1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            JLT1Aws = JPETLData1Aws[:2856]
            JLTAws = JPETLData1Aws[2856:]
            # sampled 3 weeks
            weeks.append(JLT1Aws)
            # ground truth
            ground_data = JLTAws

        if vm == "m":
            # load data for jps on AWS xlarge
            #Jpet succesful requests
            JPETM1Aws = open('./AWS/Jpet-AWS/AWS-JPS-XL.txt',"rb")
            JPETMData1Aws = np.loadtxt(JPETM1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            JMT1Aws = JPETMData1Aws[:2060]
            JMTAws = JPETMData1Aws[2060:]
            # sampled 3 weeks
            weeks.append(JMT1Aws)
            # ground truth
            ground_data = JMTAws

        if vm == "s":
            # load data for jps on AWS large
            #Jpet succesful requests
            JPETS1Aws = open('./AWS/Jpet-AWS/AWS-JPS-L.txt',"rb")
            JPETSDataAws = np.loadtxt(JPETS1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            JST1Aws = JPETSDataAws[:2830]
            JSTAws = JPETSDataAws[2830:]
            # sampled 3 weeks
            weeks.append(JST1Aws)
            # ground truth
            ground_data = JSTAws

    if (bench == "ycsb") and (platform == "aws"):
        if vm == "l":
            # load data for ycsb on AWS 2Xlarge
            YCSBLAws = open('./AWS/YCSB-AWS/AWS-YCSB-2XL.txt',"rb")
            YCSBLDataAws = np.loadtxt(YCSBLAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            YLT1Aws = YCSBLDataAws[:2371]
            YLTAws = YCSBLDataAws[2371:]
            # sampled 3 weeks
            weeks.append(YLT1Aws)
            # ground truth
            ground_data = YLTAws

        if vm == "m":
            # load data for ycsb on AWS Xlarge
            YCSBMAws = open('./AWS/YCSB-AWS/AWS-YCSB-XL.txt',"rb")
            YCSBMDataAws = np.loadtxt(YCSBMAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            YMT1Aws = YCSBMDataAws[:2402]
            YMTAws = YCSBMDataAws[2402:]
            # sampled 3 weeks
            weeks.append(YMT1Aws)
            # ground truth
            ground_data = YMTAws

        if vm == "s":
            # load data for ycsb on AWS large
            YCSBSAws = open('./AWS/YCSB-AWS/AWS-YCSB-L.txt',"rb")
            YCSBSDataAws = np.loadtxt(YCSBSAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            YST1Aws = YCSBSDataAws[:3271]
            YSTAws = YCSBSDataAws[3271:]
            # sampled 3 weeks
            weeks.append(YST1Aws)
            # ground truth
            ground_data = YSTAws

    if (bench == "tpcc") and (platform == "aws"):
        if vm == "l":
            # load data for tpcc on AWS 2Xlarge
            OLTPLAws = open('./AWS/TPCC-AWS/AWS-TPCC-2XL.txt',"rb")
            OLTPLDataAws = np.loadtxt(OLTPLAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            OLT1Aws = OLTPLDataAws[:2102]
            OLTAws = OLTPLDataAws[2102:]
            # sampled 3 weeks
            weeks.append(OLT1Aws)
            # ground truth
            ground_data = OLTAws

        if vm == "m":
            # load data for tpcc on AWS Xlarge
            OLTPMAws = open('./AWS/TPCC-AWS/AWS-TPCC-XL.txt',"rb")
            OLTPMDataAws = np.loadtxt(OLTPMAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            OMT1Aws = OLTPMDataAws[:2092]
            OMTAws = OLTPMDataAws[2092:]
            # sampled 3 weeks
            weeks.append(OMT1Aws)
            # ground truth
            ground_data = OMTAws

        if vm == "s":
            # load data for tpcc on AWS Xlarge
            OLTPSAws = open('./AWS/TPCC-AWS/AWS-TPCC-L.txt',"rb")
            OLTPSDataAws = np.loadtxt(OLTPSAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            OST1Aws = OLTPSDataAws[:2067]
            OSTAws = OLTPSDataAws[2067:]
            # sampled 3 weeks
            weeks.append(OST1Aws)
            # ground truth
            ground_data = OSTAws

    if (bench == "ima") and (platform == "aws"):
        if vm == "l":
            # load data for ima on AWS 2Xlarge
            MEMORYL1Aws = open('./AWS/IMA-AWS/AWS-IMA-2XL.txt',"rb")
            MEMORYLDataAws = np.loadtxt(MEMORYL1Aws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            MLT1Aws = MEMORYLDataAws[:2414]
            MLTAws = MEMORYLDataAws[2414:]
            # sampled 3 weeks
            weeks.append(MLT1Aws)
            # ground truth
            ground_data = MLTAws

        if vm == "m":
            # load data for ima on AWS 2Xlarge
            MEMORYMAws = open('./AWS/IMA-AWS/AWS-IMA-XL.txt',"rb")
            MEMORYMDataAws = np.loadtxt(MEMORYMAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            MMT1Aws = MEMORYMDataAws[:2643]
            MMTAws = MEMORYMDataAws[2643:]
            # sampled 3 weeks
            weeks.append(MMT1Aws)
            # ground truth
            ground_data = MMTAws

        if vm == "s":
            MEMORYSAws = open('./AWS/IMA-AWS/AWS-IMA-L.txt',"rb")
            MEMORYSDataAws = np.loadtxt(MEMORYSAws,
                                       unpack=True,
                                       delimiter=',',
                                       skiprows=0)

            MST1Aws = MEMORYSDataAws[:1706]
            MSTAws = MEMORYSDataAws[1706:]
            # sampled 3 weeks
            weeks.append(MST1Aws)
            # ground truth
            ground_data = MSTAws




    return {"weeks":weeks, "ground_data":ground_data}
