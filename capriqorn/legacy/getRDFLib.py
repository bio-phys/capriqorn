import numpy as np
# get rdf from histograms

def readNameList(nameFileName):
    nameList=[]
    fp=open(nameFileName, 'r')
    raw=fp.readlines()
    fp.close
    nameList=[name.strip('\n') for name in raw]
    return nameList


def getHistoInfo(infoFileNameList):
    data=[]
    print 
    for name in infoFileNameList:  
        print "", name
        fp=open(name, 'r')
        raw=fp.readlines()
        dummy=[line.strip('\n') for line in raw]
        data.append(dummy)
        fp.close()

    for i in range(len(data)):
        for j in range(len(data[i])):
            if data[i][j][0]!="#":
                data[i][j]=map(float, data[i][j].split())
            else:
                data[i][j]=data[i][j].split()
    info=[]
    for i in range(len(data)):
        info.append({'name': data[i][0][1], 'data' : data[i][2:]})
    return info
