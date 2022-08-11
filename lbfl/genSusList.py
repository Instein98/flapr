import os
import json
import re
from datetime import datetime

methodLevelDataDir = '/home/yicheng/research/flapr/flapr/method_level'
ochiaiResultDir = '/home/yicheng/research/flapr/d4jOchiai/results/'
outputDir = 'lbflResult'

pidList = ['Chart', 'Lang', 'Math', 'Time', 'Closure', 'Mockito']
flNameList = ['FLUCSS', 'TRAPT', 'Metallaxis', 'MUSE', 'PageRank']  # Grace, ProFL have different format

def readMethodInfo():
    methodInfoDict = {}
    methodInfoDir = os.path.join(methodLevelDataDir, 'MethodInfo')
    for pid in pidList:
        pidPath = os.path.join(methodInfoDir, pid)
        if not os.path.isdir(pidPath):
            continue
        for file in os.listdir(pidPath):
            if not file.endswith('-methodInfo.csv'):
                continue
            bid = file[:file.index('-methodInfo.csv')]
            filePath = os.path.join(pidPath, file)
            methodList = readMethodInfoForProj(filePath)
            methodInfoDict[pid + '-' + bid] = methodList
    return methodInfoDict

def readMethodInfoForProj(methodInfoFilePath: str):
    methodList = []
    with open(methodInfoFilePath, 'r') as file:
        for line in file:
            methodList.append(line.strip().split(',')[2])
    return methodList

def genMethodLevelSusList(flName: str, methodInfoDict: list):
    MethodSusListDict = {}
    if flName not in flNameList:
        err('Invalid FL name: {}'.format(flName))
        return None
    flDir = os.path.join(methodLevelDataDir, flName)
    for pid in pidList:
        pidPath = os.path.join(flDir, pid)
        if not os.path.isdir(pidPath):
            continue
        for file in os.listdir(pidPath):
            if not file.endswith('.csv'):
                continue
            filePath = os.path.join(pidPath, file)
            if flName == 'PageRank':
                if '-pk-' not in file:
                    continue
                pattern = r'.*?(\d+)-pk-.*'
            else:
                pattern = r'.*?(\d+)-.*'
            m = re.match(pattern, file)
            if m is None:
                err("File name {} does not match pattern {}".format(file, pattern))
                return None
            bid = m[1]
            print('---- {}-{} ----'.format(pid, bid))
            # read csv file
            key = pid + '-' + bid
            scoreList = []
            with open(filePath, 'r') as f:
                idx = 0
                for line in f:
                    try:
                        float(line.strip())
                    except:
                        continue
                    scoreList.append((methodInfoDict[key][idx], float(line.strip())))
                    idx += 1
            scoreList = sorted(scoreList, key=lambda x: x[1], reverse=True)
            # susList = [ x[0] for x in scoreList ]
            MethodSusListDict[key] = scoreList
    return MethodSusListDict

def translateMethodId(descMethodId: str):
    """
    Translate "org.jfree.chart.plot.CategoryPlot:setRenderer(ILorg/jfree/chart/renderer/category/CategoryItemRenderer;Z)V" to "org.jfree.chart.plot.CategoryPlot#setRenderer(int,org.jfree.chart.renderer.category.CategoryItemRenderer,boolean)"
    """
    idx = descMethodId.index('(')
    idx2 = descMethodId.index(')')
    parameter = descMethodId[idx+1: idx2]
    res = descMethodId[:idx+1].replace(':', '#')
    curArrDim = 0
    tmp = ''
    needMore = False
    for i in range(len(parameter)):
        c = parameter[i]
        if not needMore:
            if c == 'I':
                res += 'int'
            elif c == 'Z':
                res += 'boolean'
            elif c == 'B':
                res += 'byte'
            elif c == 'C':
                res += 'char'
            elif c == 'D':
                res += 'double'
            elif c == 'F':
                res += 'float'
            elif c == 'J':
                res += 'long'
            elif c == 'S':
                res += 'short'
            elif c == '[':
                curArrDim += 1
                continue
        if c == 'L':
            needMore = True
        elif c == ';':
            needMore = False
            slashClassName = tmp[1:]
            res += slashClassName.replace('/', '.')
            tmp = ''
        if needMore:
            tmp += c
            continue
        for j in range(curArrDim):
            res += '[]'
            curArrDim = 0
        res += ','
    if res.endswith(','):
        res = res[:-1]
    return res + ')'
    

def genStmtLevelSusList(methodSusListDict: dict, ochiaiDict: dict):
    stmtLevelSusDict = {}
    for key in ochiaiDict:
        if key not in methodSusListDict:
            err('Key {} not found in methodSusListDict'.format(key))
            continue
        stmtSusList = []
        scoreList = methodSusListDict[key]
        for (methodId, score) in scoreList:
            methodId = translateMethodId(methodId)
            methodId = methodId.replace('$', '.')  # for fuzzy matching
            for (omid, oscore) in ochiaiDict[key]:
                omid = omid.replace('$', '.')  # for fuzzy matching
                if omid.startswith(methodId):
                    stmtSusList.append((omid, score + 0.01 * oscore)) # calculating the new score
        stmtLevelSusDict[key] = stmtSusList
    return stmtLevelSusDict

def readOchiaiRanking():
    ochiaiDict = {}
    for pid in os.listdir(ochiaiResultDir):
        pidPath = os.path.join(ochiaiResultDir, pid)
        if not os.path.isdir(pidPath):
            continue
        for bid in os.listdir(pidPath):
            bidPath = os.path.join(pidPath, bid)
            if not os.path.isdir(bidPath):
                continue
            if pid == 'Closure' and int(bid) > 133:
                continue
            susFilePath = os.path.join(bidPath, 'ochiai.ranking.csv')
            if not os.path.isfile(susFilePath):
                err('File not found: {}'.format(susFilePath))
                continue
            
            # read suspicious list
            susList = []
            with open(susFilePath, 'r') as f:
                firstLine = True
                for line in f:
                    if firstLine:
                        firstLine = False
                        continue
                    tmp = line.strip().split(';')
                    susList.append((tmp[0], float(tmp[1])))
            key = pid + '-' + bid
            ochiaiDict[key] = susList
    return ochiaiDict

def outputStmtLevelSusList(stmtSusDict: dict, flName: str):
    for key in stmtSusDict:
        tmp = key.split('-')
        pid = tmp[0]
        bid = tmp[1]
        dir = os.path.join(outputDir, pid, bid)
        os.makedirs(dir, exist_ok=True)
        outputFilePath = os.path.join(dir, flName + '.csv')
        with open(outputFilePath, 'w') as file:
            file.write('CodeElement, SuspiciousScore\n')
            for codeElement, score in stmtSusDict[key]:
                file.write('{}, {}\n'.format(codeElement, score))

def generateStmtlevelSusListForLBFL(methodInfoDict:dict, ochiaiSusDict: dict, flName: str):
    print('===== Start {} ====='.format(flName))
    methodSusListDict = genMethodLevelSusList(flName, methodInfoDict)
    stmtSusDict = genStmtLevelSusList(methodSusListDict, ochiaiSusDict)
    outputStmtLevelSusList(stmtSusDict, flName)

def err(msg: str):
    print('[ERROR]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def warn(msg: str):
    print('[WARNING]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def log(msg: str):
    print('[INFO]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

if __name__ == '__main__':
    methodInfoDict = readMethodInfo()
    ochiaiDict = readOchiaiRanking()
    # generateStmtlevelSusListForLBFL(methodInfoDict, ochiaiDict, 'TRAPT')
    for fl in flNameList:
        generateStmtlevelSusListForLBFL(methodInfoDict, ochiaiDict, fl)
    # # print(methodInfoDict)
    # with open('tmp2', 'w') as file:
    #     json.dump(stmtSusDict, file, indent=2)
    # print(translateMethodId('org.apache.commons.lang.time.FastDateFormat:getDateTimeInstance(IILjava/util/Locale;)Lorg/apache/commons/lang/time/FastDateFormat;'))
