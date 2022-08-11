import os
import sys
import math
import json
import argparse
from datetime import datetime
from prettytable import PrettyTable

def readD4j120BuggyPos():
    res = {}  # {bugId: list of locations}
    with open(d4jBuggyPosFile, 'r') as file:
        for line in file:
            tmp = line.strip().split('@')
            bugId = tmp[0].replace('_', '-')
            location = tmp[1]
            if '/org/' in location:
                index = location.index('/org/') + 1
            elif '/com/' in location:
                index = location.index('/com/') + 1
            dotClassName = location[index:-5].replace('/', '.')
            lineNum = tmp[2]

            if bugId not in res:
                res[bugId] = []
            res[bugId].append(dotClassName + ':' + lineNum)
    return res

patchesInfoDir = 'praprPatchesInfo'
flSusListDir = '../sbfl/sbflResult/'
gzoltarFLSusListDir = '/home/yicheng/research/flapr/d4jOchiai/results/'
simulateReportDir = 'simulateReport'
d4jBuggyPosFile = 'd4j120fixPos.txt'
d4jBuggyStmtDict = readD4j120BuggyPos()

fls = ["Ample", "Anderberg", "Dice", "Dstar2", "ER1a", "ER1b", "ER5c", "Euclid", "Goodman", 
        "GP02", "GP03", "GP13", "GP19", "Hamann", "Hamming", "Jaccard", "Kulczynski1", 
        "Kulczynski2", "M1", "M2", "Ochiai", "Ochiai2", "Overlap", "rensenDice", 
        "RogersTanimoto", "RussellRao", "SBI", "SimpleMatching", "Sokal", "Tarantula", 
        "Wong1", "Wong2", "Wong3", "Zoltar"]

def getProjHavingCorrectPatch():
    res = []
    for pid in os.listdir(patchesInfoDir):
        pidPath = os.path.join(patchesInfoDir, pid)
        if not os.path.isdir(pidPath):
            continue
        for jsonFile in os.listdir(pidPath):
            if not jsonFile.endswith('.json'):
                continue
            jsonFilePath = os.path.join(pidPath, jsonFile)
            with open(jsonFilePath, 'r') as file:
                if '"isCorrect": true' in file.read():
                    bid = jsonFile[:-5]
                    res.append(pid + '-' + bid)
    return res

def translateGzoltarLocation(loc: str):
    """
    org.apache.commons.lang3.math$NumberUtils#createNumber(java.lang.String):570 ->
    org.apache.commons.lang3.math.NumberUtils:570
    """
    tmp = loc.split(':')
    lineNumber = tmp[1]
    className = tmp[0]
    # only change the first $ to .
    className = className[:className.index('#')].replace('$', '.', 1)
    return className + ':' + lineNumber

def readSusList(pid: str, bid: str, flName: str, isGzoltar=False):
    if isGzoltar:
        flName = flName.lower()
        if flName == 'dstar2':
            flName = 'dstar'
        elif flName == 'rensendice':
            flName = 'sorensendice'
        elif flName == 'russellrao':
            flName = 'russelrao'
        susListPath = os.path.join(gzoltarFLSusListDir, pid, bid, flName + '.ranking.csv')
        delimiter = ';'
    else:
        susListPath = os.path.join(flSusListDir, pid, bid, flName + '.csv')
        delimiter = ', '
    if not os.path.isfile(susListPath):
        err('File not found: {}'.format(susListPath))
        return None
    res = []  # list of [location, score, rank]
    firstLine = True
    with open(susListPath, 'r') as file:
        for line in file:
            if firstLine:
                firstLine = False
                continue
            if delimiter in line:
                tmp = line.strip().split(delimiter)
                location = tmp[0]
                if isGzoltar:
                    location = translateGzoltarLocation(location)
                score = float(tmp[1])
                res.append([location, score, len(res)+1])
    
    # if two stmts have the same score, their rank should both set to the lower one.
    lastScore = -1
    idxTied = []
    for i in range(len(res)):
        curScore = res[i][1]
        if lastScore == -1:
            lastScore = curScore
            continue
        if math.isclose(curScore, lastScore, abs_tol=0.0000001):
            idxTied.append(i-1)
            if i == len(res) - 1:
                idxTied.append(i)
        else:
            for idx in idxTied:
                res[idx][2] = i
            idxTied.clear()
        lastScore = curScore
    for idx in idxTied:
        res[idx][2] = len(res)
    res = [(x[0], x[2]) for x in res]
    return res

def readPatchInfoDict(pid: str, bid: str, CBeforeP=True):
    """
    If CBeforeP, correct patches are sorted before the plausible patches, otherwise sorted after.
    """
    # read the patches information
    patchInfoPath = os.path.join(patchesInfoDir, pid, bid + '.json')
    if not os.path.isfile(patchInfoPath):
        err('File not found: {}'.format(patchInfoPath))
        return None
    with open(patchInfoPath, 'r') as file:
        patchesDict = json.load(file)
    
    # sort the patches (Assume for each location, correct is generated before plausible patches and implausible patches)
    # For each location, sort the correct before plausible, plausible before implausible.
    for location in patchesDict:
        patchList = patchesDict[location]
        patchList = sortPatches(patchList, CBeforeP)
        patchesDict[location] = patchList
    return patchesDict

def sortPatches(listOfPatches: list, CBeforeP: bool):
    correctPatchList = []
    plausiblePatchList = []  # plausible but not correct
    for patch in listOfPatches:
        if patch['isCorrect'] == True:
            correctPatchList.append(patch)
            continue
        elif patch['isPlausible'] == True:
            plausiblePatchList.append(patch)
            continue
    for patch in plausiblePatchList: 
        listOfPatches.remove(patch)
        if CBeforeP:
            listOfPatches.insert(0, patch)
        else:
            listOfPatches.append(patch)
    for patch in correctPatchList:
        listOfPatches.remove(patch)
        if CBeforeP:
            listOfPatches.insert(0, patch)
        else:
            listOfPatches.append(patch)
    return listOfPatches

def sortPatchesByFL(susList: list, patchesDict: dict, CBeforeP=True):
    """
    Sort the patches according to the ranks of the statements generating them on the FL's suspicious list
    Note that the ranks of some statements can tie, so there is no clear order of the patches generated by them,
    in that case, such patches are gathered together and reordered so that the rank: correct < plausible < implausible
    (smaller rank implies the patches are generated earlier)
    """
    res = []  # list of the patches generated using the FL order.
    
    # sort the locations according to the fl suspicious list
    lastRank = -1
    tiedLocPatches = []
    tiedLocNum = 0
    for (location, rank) in susList: 
        if lastRank == -1:
            if location in patchesDict:
                lastRank = rank
                tiedLocNum += 1
                tiedLocPatches.extend(patchesDict[location])
            continue
        if rank == lastRank:
            if location in patchesDict:
                tiedLocNum += 1
                tiedLocPatches.extend(patchesDict[location])
            continue
        else:  # rank != lastRank
            if tiedLocNum > 1:  # the correct must already be sorted before plausible
                # sort correct before plausible
                tiedLocPatches = sortPatches(tiedLocPatches, CBeforeP)
            res.extend(tiedLocPatches)
            tiedLocPatches.clear()
            tiedLocNum == 0
            lastRank = rank
            if location in patchesDict:
                tiedLocNum += 1
                tiedLocPatches.extend(patchesDict[location])
            continue
    if len(tiedLocPatches) != 0:
        if tiedLocNum > 1:  # the correct must already be sorted before plausible
            # sort correct before plausible
            tiedLocPatches = sortPatches(tiedLocPatches, CBeforeP)
        res.extend(tiedLocPatches)
    return res

def orderOfCorrectPlausible(patchOrderedList: list):
    res = []
    for patch in patchOrderedList:
        if patch['isCorrect'] == True:
            res.append(1)
        elif patch['isPlausible'] == True:
            res.append(0)
    return res

def timeToGenFirstCorrect(patchOrderedList: list):
    res = 0
    for patch in patchOrderedList:
        if patch['isCorrect'] == False:
            res += patch['validationTime']
        else:
            return res
    return -1  # -1 means no correct patch is found

def numOfPlausibleBeforeCorrect(simplifiedOrder):  # the argument is a list of 0s and 1s generated by orderOfCorrectPlausible()
    res = 0
    for x in simplifiedOrder:
        if x == 1:
            return res
        else:
            res += 1
    return -1  # -1 means no correct patch is found

def firstBuggyStmtRankInSusList(pid: str, bid: str, susList: list):
    bugId = pid + '-' + bid
    if bugId not in d4jBuggyStmtDict:
        err('The buggy position of {}-{} not found in {}'.format(pid, bid, d4jBuggyPosFile))
        return None
    buggyLocList = d4jBuggyStmtDict[bugId]
    for i in range(len(susList)):
        if susList[i][0] in buggyLocList:
            return susList[i][1]
    return -1  # -1 means no buggy location found in the suspicious list

def getFirstPlausibleInducingStmtRank(patchOrderedList: list, susList: list, includeCorrect: bool):
    for patch in patchOrderedList:
        if patch['isPlausible'] == True or patch['isCorrect'] == True:
            if (not includeCorrect) and patch['isCorrect'] == True:
                continue
            mutatedClass = patch['mutatedClass']
            lineNumber = patch['lineNumber']
            location = mutatedClass + ':' + lineNumber
            for (loc, rank) in susList:
                if location == loc:
                    return rank
    return -1  # -1 means no statement satisfying the requirement is found

def generateSummary(pid: str, bid: str, prettyTable=False, isGzoltar=False):
    log('===== Processing {}-{} ====='.format(pid, bid))
    text = 'FL, P&C Distribution, #P before C, TimeToFind1stC, 1stBuggyRank, 1stPorCRank, 1stPnoCRank\n'
    patchInfoDict = readPatchInfoDict(pid, bid)
    if patchInfoDict is None:
        err('Failed to read patches info for {}-{}, skipping'.format(pid, bid))
        return
    for fl in fls:
        susList = readSusList(pid, bid, fl, isGzoltar)  # list of (location, rank)
        if susList is None:
            err('Failed to read the suspicious list of FL {2} for {0}-{1}, skipping {2}'.format(pid, bid, fl))
            continue
        firstBuggyRank = firstBuggyStmtRankInSusList(pid, bid, susList)
        patchOrderedList = sortPatchesByFL(susList, patchInfoDict)
        if patchOrderedList is None:
            err('Failed to sort patches according to the FL {0}, skipping {0}'.format(fl))
            continue
        firstPlausibleNotCorrectRank = getFirstPlausibleInducingStmtRank(patchOrderedList, susList, False)  # The rank of the first plausible-inducing stmt in susList (exclude correct)
        firstPlausibleOrCorrectRank = getFirstPlausibleInducingStmtRank(patchOrderedList, susList, True)  # The rank of the first plausible-inducing stmt in susList (include correct)
        distributionList = orderOfCorrectPlausible(patchOrderedList)
        numPBeforeC = numOfPlausibleBeforeCorrect(distributionList)
        timeForFirstC = timeToGenFirstCorrect(patchOrderedList)
        distributionStr = str(distributionList)[1:-1].replace(', ', '-').replace('1', 'X').replace('0', 'O')
        text += '{}, {}, {}, {}, {}, {}, {}\n'.format(fl, distributionStr, numPBeforeC, timeForFirstC, firstBuggyRank, firstPlausibleOrCorrectRank, firstPlausibleNotCorrectRank)
    os.makedirs(os.path.join(simulateReportDir, pid), exist_ok=True)
    with open(os.path.join(simulateReportDir, pid, bid + '.report'), 'w') as file:
        if prettyTable:
            text = csvToPrettyTable(text)
        file.write(text)

def csvToPrettyTable(text: str):
    table = None
    firstLine = True
    for line in text.split('\n'):
        if firstLine:
            table = PrettyTable(line.split(', '))
            firstLine = False
            continue
        if ', ' in line:
            # print(line.split(', '))
            table.add_row(line.split(', '))
    return table.get_string()

def main():
    for projId in getProjHavingCorrectPatch():
        tmp = projId.split('-')
        pid = tmp[0]
        bid = tmp[1]
        generateSummary(pid, bid, prettyTable=True, isGzoltar=True)

def err(msg: str):
    print('[ERROR]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def warn(msg: str):
    print('[WARNING]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def log(msg: str):
    print('[INFO]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

if __name__ == '__main__':
    main()
    # readSusList('Chart', '1', 'Ochiai')