"""
Generating suspicious list using different SBFL techniques.
"""

import os
import math
from pathlib import Path

exeInfoDir = 'sbflExeInfo'
sbflResultDir = 'sbflResult'


# Formulae

def Tarantula(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS / totalFail
    denominator = failS / totalFail + passS / totalPass
    return numerator / denominator

def Ample(passS: int, failS: int, totalPass: int, totalFail: int):
    tmp1 = failS / totalFail
    tmp2 = passS / totalPass
    return abs(tmp1 - tmp2)

def rensenDice(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = 2 * failS
    denominator = 2 * failS + passS + (totalFail - failS)
    return numerator / denominator

def Kulczynski2(passS: int, failS: int, totalPass: int, totalFail: int):
    tmp1 = failS / totalFail
    tmp2 = failS / (failS + passS)
    return (tmp1 + tmp2) / 2

def M1(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS + (totalPass - passS)
    demoninator = (totalFail - failS) + passS
    return numerator / demoninator

def Goodman(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = 2*failS - (totalFail - failS) - passS
    denominator = 2*failS + (totalFail - failS) + passS
    return numerator / denominator

def Overlap(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS
    denominator = min(failS, passS, (totalFail - failS))
    return numerator / denominator

def Zoltar(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS
    denominator = totalFail + passS + (10000*(totalFail-failS)*passS) / failS
    return numerator / denominator

def ER5c(passS: int, failS: int, totalPass: int, totalFail: int):
    if failS < totalFail:
        return 0
    elif failS == totalFail:
        return 1

def GP13(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS * (1 + 1 / (2*passS + failS))

def Dstar2(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS ** 2
    denominator = passS + (totalFail - failS)
    return numerator / denominator

def ER1a(passS: int, failS: int, totalPass: int, totalFail: int):
    if failS < totalFail:
        return -1
    elif failS == totalFail:
        return totalPass - passS

def Ochiai(passS: int, failS: int, totalPass: int, totalFail: int):
    denominator = math.sqrt(totalFail * (failS + passS))
    return failS / denominator

def RussellRao(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS / (totalFail + totalPass)

def Dice(passS: int, failS: int, totalPass: int, totalFail: int):
    return 2 * failS / (totalFail + passS)

def SimpleMatching(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS + (totalPass - passS)
    return numerator / (totalFail + totalPass)

def M2(passS: int, failS: int, totalPass: int, totalFail: int):
    denominator = failS + (totalPass - passS) + 2*(totalFail - failS) + 2*passS
    return failS / denominator

def Hamming(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS + (totalPass - passS)

def Anderberg(passS: int, failS: int, totalPass: int, totalFail: int):
    denominator = failS + 2*(totalFail - failS) + 2*passS
    return failS / denominator

def Wong1(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS

def GP02(passS: int, failS: int, totalPass: int, totalFail: int):
    return 2*(failS + math.sqrt(totalPass)) + math.sqrt(passS)

def GP19(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS * math.sqrt(abs( passS - failS + totalFail - totalPass ))

def Wong3(passS: int, failS: int, totalPass: int, totalFail: int):
    if passS <= 2:
        h = passS
    elif 2 < passS <= 10:
        h = 2 + 0.1 * (passS - 2)
    elif passS > 10:
        h = 2.8 + 0.01 * (passS - 10)
    return failS - h

def ER1b(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS - passS / (totalPass + 1)

def Jaccard(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS / (totalFail + passS)

def Hamann(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS + (totalPass - passS) - passS - (totalFail - failS)
    return numerator / (totalFail + totalPass)

def Kulczynski1(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS / ((totalFail - failS) + passS)

def Sokal(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = 2 * (failS) + 2 * (totalPass - passS)
    denominator = 2*failS + 2*(totalPass - passS) + (totalFail - failS) + passS
    return numerator / denominator

def RogersTanimoto(passS: int, failS: int, totalPass: int, totalFail: int):
    numerator = failS + (totalPass - passS)
    denominator = failS + (totalPass - passS) + 2*(totalFail - failS) + 2*passS
    return numerator / denominator

def Euclid(passS: int, failS: int, totalPass: int, totalFail: int):
    return math.sqrt(failS + (totalPass - passS))

def Ochiai2(passS: int, failS: int, totalPass: int, totalFail: int):
    pass_ = totalPass - passS
    fail_ = totalFail - failS
    numerator = failS * pass_
    denominator = math.sqrt((failS + passS) * (fail_ + pass_) * (failS + pass_) * (fail_ + passS))
    return numerator / denominator

def Wong2(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS - passS

def GP03(passS: int, failS: int, totalPass: int, totalFail: int):
    return math.sqrt(abs(failS**2 - math.sqrt(passS)))

def SBI(passS: int, failS: int, totalPass: int, totalFail: int):
    return failS / (failS + passS)

# def op2(passS: int, failS: int, totalPass: int, totalFail: int):
#     tmp = passS / (totalPass + 1)
#     return failS - tmp

# def barinel(passS: int, failS: int, totalPass: int, totalFail: int):
#     tmp = passS / (passS + failS)
#     return 1 - tmp

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
    fls = [Ample, Anderberg, Dice, Dstar2, ER1a, ER1b, ER5c, Euclid, Goodman, 
            GP02, GP03, GP13, GP19, Hamann, Hamming, Jaccard, Kulczynski1, 
            Kulczynski2, M1, M2, Ochiai, Ochiai2, Overlap, rensenDice, 
            RogersTanimoto, RussellRao, SBI, SimpleMatching, Sokal, Tarantula, 
            Wong1, Wong2, Wong3, Zoltar]
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