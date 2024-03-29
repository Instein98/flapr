from bdb import effective
import os
import math
import json
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
lbflSusListDir = '../lbfl/lbflResult/'
gzoltarFLSusListDir = '/home/yicheng/research/flapr/d4jOchiai/results/'
simulateReportDir = 'simulateReport'
d4jBuggyPosFile = 'd4j120fixPos.txt'
d4jBuggyStmtDict = readD4j120BuggyPos()

sbfls = ["Ample", "Anderberg", "Dice", "Dstar2", "ER1a", "ER1b", "ER5c", "Euclid", "Goodman", 
        "GP02", "GP03", "GP13", "GP19", "Hamann", "Hamming", "Jaccard", "Kulczynski1", 
        "Kulczynski2", "M1", "M2", "Ochiai", "Ochiai2", "Overlap", "rensenDice", 
        "RogersTanimoto", "RussellRao", "SBI", "SimpleMatching", "Sokal", "Tarantula", 
        "Wong1", "Wong2", "Wong3", "Zoltar"]
lbfls = ['FLUCSS', 'TRAPT', 'Metallaxis', 'MUSE', 'PageRank', 'Grace', 'ProFL']

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

def readSusList(pid: str, bid: str, flName: str, lbfl=False, isGzoltar=False):
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
        if lbfl:
            susListPath = os.path.join(lbflSusListDir, pid, bid, flName + '.csv')
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

def readPatchInfoDict(pid: str, bid: str, CBeforeP=False):
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

def recalculateSusListRank(newSusList: list):
    lastRank = -1
    rankCounter = 0
    tiedIndex = []
    for i in range(len(newSusList)):
        (loc, rank) = newSusList[i]
        if lastRank == -1:
            lastRank = rank
            tiedIndex.append(i)
            rankCounter += 1
            continue
        else:
            if rank == lastRank:
                tiedIndex.append(i)
                rankCounter += 1
            else:
                # assign the tiedIndex with rankCounter
                for idx in tiedIndex:
                    newSusList[idx] = (newSusList[idx][0], rankCounter)
                # update variables
                lastRank = rank
                rankCounter += 1
                tiedIndex.clear()
                tiedIndex.append(i)
    for idx in tiedIndex:
        newSusList[idx] = (newSusList[idx][0], rankCounter)
    return newSusList

def getEffectiveSusList(susList: list, patchesDict: dict):
    effectiveSusList = list(susList)
    patchLocs = [ l for l in patchesDict ]
    patchLocSet = set(patchLocs)
    removeList = []
    for (loc, rank) in effectiveSusList:
        if loc not in patchLocSet:
            removeList.append((loc, rank))
    for item in removeList:
        effectiveSusList.remove(item)
    return recalculateSusListRank(effectiveSusList)

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

def getFirstCorrectPatchRank(patchOrderedList: list):
    count = 0
    for patch in patchOrderedList:
        count += 1
        if patch['isCorrect'] == True:
            return count
    return -1

def getFirstPlausiblePatchRank(patchOrderedList: list):
    count = 0
    for patch in patchOrderedList:
        count += 1
        if patch['isPlausible'] == True and patch['isCorrect'] == False:  # exclude correct patches
            return count
    return -1

def getTieStatus(susList: list, topNum=5):
    res = []
    lastRank = -1
    count = 0
    for (location, rank) in susList: 
        if lastRank == -1:
            lastRank = rank
            count = 1
        elif rank == lastRank:
            count += 1
        else:  # rank != lastRank
            res.append((lastRank, count))
            if len(res) >= topNum:
                break
            lastRank = rank
            count = 1
    if len(res) < topNum:
        res.append((lastRank, count))

    output = ''
    for (rank, count) in res:
        output += '{}*{};'.format(count, rank)
    return output[:-1]

def getAvgTieStmtNum(susList: list):
    tieNumList = []
    lastRank = -1
    count = 0
    for (location, rank) in susList: 
        if lastRank == -1:
            lastRank = rank
            count = 1
        elif rank == lastRank:
            count += 1
        else:  # rank != lastRank
            tieNumList.append(count)
            lastRank = rank
            count = 1
    tieNumList.append(count)
    return round(sum(tieNumList) / len(tieNumList), 2)

def getAvgTiePatchNum(susList: list, patchInfoDict: dict):
    tieNumList = []
    lastRank = -1
    count = 0
    for (location, rank) in susList: 
        if lastRank == -1:
            lastRank = rank
            if location in patchInfoDict:
                count = len(patchInfoDict[location])
            else:
                count = 0
        elif rank == lastRank:
            if location in patchInfoDict:
                count += len(patchInfoDict[location])
        else:  # rank != lastRank
            tieNumList.append(count)
            lastRank = rank
            if location in patchInfoDict:
                count = len(patchInfoDict[location])
            else:
                count = 0
    tieNumList.append(count)
    return round(sum(tieNumList) / len(tieNumList), 2)

def jsonDump(obj, file):
    with open(file, 'w') as f:
        json.dump(obj, f, indent=4)

class Table:
    def __init__(self, pid, bid, columnNameList, flNameList, patchInfoDict, CBeforeP=True):
        self.pid = pid
        self.bid = bid
        self.columnNameList = columnNameList
        self.flNameList = flNameList
        self.patchInfoDict = patchInfoDict
        self.table = {}  # FL: [values]
        self.calculated = False
        self.CBeforeP = CBeforeP
        for fl in self.flNameList:
            self.table[fl] = []

    def calculateCells(self):
        for fl in self.flNameList:
            # Preparation
            if fl in sbfls:
                susList = readSusList(self.pid, self.bid, fl, isGzoltar=True)  # list of (location, rank)
            elif fl in lbfls:
                susList = readSusList(self.pid, self.bid, fl, lbfl=True)  # list of (location, rank)
            if susList is None:
                err('Failed to read the suspicious list of FL {2} for {0}-{1}, skipping {2}'.format(self.pid, self.bid, fl))
                self.table[fl] = ['ERROR' for i in range(len(self.columnNameList)-1)]
                continue

            patchOrderedList = sortPatchesByFL(susList, self.patchInfoDict, self.CBeforeP)
            if patchOrderedList is None:
                err('Failed to sort patches according to the FL {0}, skipping {0}'.format(fl))
                self.table[fl] = ['ERROR' for i in range(len(self.columnNameList)-1)]
                continue

            for column in self.columnNameList:
                if column == 'FL':
                    continue
                elif column == '#PBeforeC':
                    distributionList = orderOfCorrectPlausible(patchOrderedList)
                    value = numOfPlausibleBeforeCorrect(distributionList)
                elif column == 'TimeToFind1stC':
                    value = timeToGenFirstCorrect(patchOrderedList)
                elif column == 'PCDistribution':
                    distributionList = orderOfCorrectPlausible(patchOrderedList)
                    value = str(distributionList)[1:-1].replace(', ', '').replace('1', 'X').replace('0', 'O')
                elif column == '1stBuggyStmtRank':
                    value = firstBuggyStmtRankInSusList(self.pid, self.bid, susList)
                elif column == '1stPorCStmtRank':  # The rank of the first plausible-inducing stmt in susList (include correct)
                    value = getFirstPlausibleInducingStmtRank(patchOrderedList, susList, True)
                elif column == '1stPnoCStmtRank':  # The rank of the first plausible-inducing stmt in susList (exclude correct)
                    value = getFirstPlausibleInducingStmtRank(patchOrderedList, susList, False)
                elif column == '1stCPatchRank':  # The rank of the first correct patch in patchOrderedList
                    value = getFirstCorrectPatchRank(patchOrderedList)
                elif column == '1stPPatchRank':  # The rank of the first plausible patch in patchOrderedList (exclude correct)
                    value = getFirstPlausiblePatchRank(patchOrderedList)
                elif column == '1stBugStmtEffRank':  # effectiveSusList: removing the stmt that can not generate patch in susList
                    effectiveSusList = getEffectiveSusList(susList, self.patchInfoDict)
                    value = firstBuggyStmtRankInSusList(self.pid, self.bid, effectiveSusList)
                elif column == 'AvgStmtTieNum':
                    value = getAvgTieStmtNum(susList)
                elif column == 'AvgPatchTieNum':
                    value = getAvgTiePatchNum(susList, self.patchInfoDict)
                elif column == 'Top5Tie':
                    value = getTieStatus(susList)
                self.table[fl].append(value)
        self.calculated = True
    
    def generateCSVText(self):
        if not self.calculated:
            self.calculateCells()
        txt = ''
        for column in self.columnNameList:
            if column == self.columnNameList[0]:
                txt += column
                continue
            txt += ', ' + column
        txt += '\n'

        for fl in self.flNameList:
            txt += fl
            for value in self.table[fl]:
                txt += ', ' + str(value)
            txt += '\n'
        return txt


def generateSummary(pid: str, bid: str, prettyTable=False, isGzoltar=False, CBeforeP=True):
    log('===== Processing {}-{} ====='.format(pid, bid))
    
    patchInfoDict = readPatchInfoDict(pid, bid, CBeforeP)
    if patchInfoDict is None:
        err('Failed to read patches info for {}-{}, skipping'.format(pid, bid))
        return

    columnList = ['FL', '#PBeforeC', 'TimeToFind1stC', '1stBuggyStmtRank', '1stPorCStmtRank', '1stBugStmtEffRank', '1stCPatchRank', '1stPPatchRank', 'AvgStmtTieNum', 'AvgPatchTieNum', 'Top5Tie']
    # columnList = ['FL', '#PBeforeC', 'TimeToFind1stC', '1stBuggyStmtRank', '1stPorCStmtRank', 'Top5Tie']
    table = Table(pid, bid, columnList, sbfls + lbfls, patchInfoDict, CBeforeP=CBeforeP)
    table.calculateCells()
    text = table.generateCSVText()

    os.makedirs(os.path.join(simulateReportDir, pid), exist_ok=True)
    setting = 'ideal' if CBeforeP else 'worst'
    with open(os.path.join(simulateReportDir, pid, bid + '-{}.csv'.format(setting)), 'w') as file:
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

def err(msg: str):
    print('[ERROR]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def warn(msg: str):
    print('[WARNING]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def log(msg: str):
    print('[INFO]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

if __name__ == '__main__':
    for projId in getProjHavingCorrectPatch():
        tmp = projId.split('-')
        pid = tmp[0]
        bid = tmp[1]
        generateSummary(pid, bid, prettyTable=False, isGzoltar=True, CBeforeP=True)
        generateSummary(pid, bid, prettyTable=False, isGzoltar=True, CBeforeP=False)

    # print(len([projId for projId in getProjHavingCorrectPatch()]))
    # readSusList('Chart', '1', 'Ochiai')
    # generateSummary('Math', '50', prettyTable=False, isGzoltar=True, CBeforeP=True)
