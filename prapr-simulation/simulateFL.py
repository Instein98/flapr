import os
import sys
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

def readSusList(pid: str, bid: str, flName: str):
    susListPath = os.path.join(flSusListDir, pid, bid, flName + '.csv')
    res = []
    firstLine = True
    with open(susListPath, 'r') as file:
        for line in file:
            if firstLine:
                firstLine = False
                continue
            if ', ' in line:
                location = line.strip().split(', ')[0]
                res.append(location)
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
        correctPatchList = []
        plausiblePatchList = []  # plausible but not correct
        for patch in patchList:
            if patch['isCorrect'] == True:
                correctPatchList.append(patch)
                continue
            elif patch['isPlausible'] == True:
                plausiblePatchList.append(patch)
                continue
        for patch in plausiblePatchList: 
            patchList.remove(patch)
            if CBeforeP:
                patchList.insert(0, patch)
            else:
                patchList.append(patch)
        for patch in correctPatchList:
            patchList.remove(patch)
            if CBeforeP:
                patchList.insert(0, patch)
            else:
                patchList.append(patch)
        patchesDict[location] = patchList
    return patchesDict

def sortPatchesByFL(susList: list, patchesDict: dict):
    res = []  # list of the patches generated using the FL order.
    
    # sort the locations according to the fl suspicious list
    for location in susList:
        if location in patchesDict:
            res.extend(patchesDict[location])
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
        if susList[i] in buggyLocList:
            return i + 1
    return -1  # -1 means no buggy location found in the suspicious list

def generateSummary(pid: str, bid: str, prettyTable=False):
    log('===== Processing {}-{} ====='.format(pid, bid))
    text = 'FL, Plausible&Correct Distribution, #Plausible before Correct, Time before First Correct, FirstBuggyRank\n'
    patchInfoDict = readPatchInfoDict(pid, bid)
    if patchInfoDict == None:
        err('Failed to read patches info for {}-{}, skipping'.format(pid, bid))
        return
    for fl in fls:
        susList = readSusList(pid, bid, fl)
        firstBuggyRank = firstBuggyStmtRankInSusList(pid, bid, susList)
        patchOrderedList = sortPatchesByFL(susList, patchInfoDict)
        if patchOrderedList == None:
            err('Failed to sort patches according to the FL {0}, skipping {0}'.format(fl))
            continue
        distributionList = orderOfCorrectPlausible(patchOrderedList)
        numPBeforeC = numOfPlausibleBeforeCorrect(distributionList)
        timeForFirstC = timeToGenFirstCorrect(patchOrderedList)
        distributionStr = str(distributionList)[1:-1].replace(', ', '-').replace('1', 'X').replace('0', 'O')
        text += '{}, {}, {}, {}, {}\n'.format(fl, distributionStr, numPBeforeC, timeForFirstC, firstBuggyRank)
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
        generateSummary(pid, bid, prettyTable=True)

def err(msg: str):
    print('[ERROR]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def warn(msg: str):
    print('[WARNING]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def log(msg: str):
    print('[INFO]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('command')
    # parser.parse_args(sys.argv[1:])
    # args = parser.parse_args(['xxx'])
    # print(vars(args))
    # generateSummary()
    # print(getProjHavingCorrectPatch())
    main()