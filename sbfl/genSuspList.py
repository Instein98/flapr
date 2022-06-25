"""
Generating suspicious list using different SBFL techniques.
"""

import os
import math
from pathlib import Path

exeInfoDir = 'sbflExeInfo'
sbflResultDir = 'sbflResult'


# Formulae

def tarantula(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS / totalFail
    denominator = failS / totalFail + passS / totalPass
    return numerator / denominator

def ochiai(passS: int, failS: int, totalPass: int, totalFail: int):
    denominator = math.sqrt(totalFail * (failS + passS))
    return failS / denominator

def op2(passS: int, failS: int, totalPass: int, totalFail: int):
    tmp = passS / (totalPass + 1)
    return failS - tmp

def barinel(passS: int, failS: int, totalPass: int, totalFail: int):
    tmp = passS / (passS + failS)
    return 1 - tmp

def produceSusList(sbfl, exeCsvFile: str, outputFilePath: str):
    if os.path.isfile(outputFilePath):
        print("{} already exists, skipping...".format(outputFilePath))
        return
    elementScoreList = [] # stores (element, score)
    with open(exeCsvFile, 'r') as file:
        firstLine = True
        for line in file:
            if firstLine:
                firstLine = False
                continue
            # CodeElement, passed(s), failed(s), totalpassed, totalfailed
            tmp = line.strip().split(', ')
            element = tmp[0]
            passS = int(tmp[1])
            failS = int(tmp[2])
            totalPass = int(tmp[3])
            totalFail = int(tmp[4])
            score = sbfl(passS, failS, totalPass, totalFail)
            elementScoreList.append((element, score))
    elementScoreList.sort(key=lambda eleAndScore: eleAndScore[1], reverse=True)

    # write result
    Path(outputFilePath).parent.mkdir(parents=True, exist_ok=True)
    with open(outputFilePath, 'w') as file:
        file.write('CodeElement, SuspiciousScore\n')
        for elementScore in elementScoreList:
            file.write('{}, {}\n'.format(elementScore[0], elementScore[1]))

def main():
    fls = [tarantula, ochiai, op2, barinel]
    for pid in os.listdir(exeInfoDir):
        pidPath = os.path.join(exeInfoDir, pid)
        if not os.path.isdir(pidPath):
            continue
        for csvFile in os.listdir(pidPath):
            if not csvFile.endswith('.csv'):
                continue
            csvFilePath = os.path.join(pidPath, csvFile)
            bid = csvFile[:-4]
            print("\n=============== processing {}-{} ===============".format(pid, bid))
            for fl in fls:
                produceSusList(fl, csvFilePath, os.path.join(sbflResultDir, pid, bid, fl.__name__ + '.csv'))


if __name__ == '__main__':
    # produceSusList(op2, '/home/yicheng/apr/flapr/sbfl/sbflExeInfo/Math/1.csv', 'tmp')
    main()