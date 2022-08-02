"""
This script is to generate a statment patch generation/validation info file for each defects4j buggy project:
Stmt, isBuggy, patches list, plausible patches list (include correct patches), correct patches list, patches generation time cost (ms), validation all patches time cost (ms)
"""

import os
import re
import json
from datetime import datetime

# the patches dir generated by tbar when generating uniapr style patches
tbarPatchesDir = '/home/yicheng/research/apr/experiments/tbar/patches'
tbarValidationResultDir = '/home/yicheng/research/flapr/flapr/validationResult'
outputDir = 'analysisResult'

projDict = {
    'Chart': (list(range(1, 27)), []),
    # 'Closure': (list(range(1, 134)), [63, 93]),  # have no patches for Closure for now
    # 'Lang': (list(range(1, 66)), [2]),
    # 'Math': (list(range(1, 107)), []),
    # 'Mockito': (list(range(1, 39)), []),
    # 'Time': (list(range(1, 28)), [21])
}

def main():
    os.makedirs(outputDir, exist_ok=True)
    for pid in projDict.keys():
        bidList, depList = projDict[pid]
        for bid in bidList:
            if bid in depList:
                continue
            bugId = str(pid) + '_' + str(bid)
            patchesInfoFile = os.path.join(tbarPatchesDir, bugId, 'patches-pool', 'patches.info')
            if not os.path.isfile(patchesInfoFile):
                err('Find not found: {}, patch generation of {} is not finished.'.format(patchesInfoFile, bugId))
                continue
            patchValidationLog = os.path.join(tbarValidationResultDir, str(pid) + '-' + str(bid) + '.validation.log')
            if not os.path.isfile(patchValidationLog):
                err('File not found: {}, patch validation of {} has not stated yet.'.format(patchValidationLog, bugId))
                continue
            with open(patchValidationLog, 'r') as file:
                if 'BUILD SUCCESS' not in file.read():
                    err('Patch validation of {} has not finished or failed.'.format(bugId))
                    continue
            print('====================')
            print('===== {} ====='.format(bugId))
            print('====================')
            stmtInfoDict = readPatchGenInfo(pid, bid, None)
            stmtInfoDict = readPatchValidationInfo(pid, bid, stmtInfoDict, patchValidationLog)
            j = json.dumps(stmtInfoDict, indent=2)
            with open(os.path.join(outputDir, bugId+'.json'), 'w') as file:
                print(j, file=file)

def readPatchGenInfo(pid: int, bid: int, stmtInfoDict: dict):
    """
    The modified tbar will generate a json patches.info file when generating uniapr style patches. This function will read the json file and get the data of stmt location, patches list, stmt process time. The structure of the result: {bugId: {stmtLocation: {key values}}}
    """
    if stmtInfoDict is None:
        stmtInfoDict = {}
    bugId = str(pid) + '_' + str(bid)

    patchesPoolDir = os.path.join(tbarPatchesDir, bugId, 'patches-pool')
    for patchPoolId in os.listdir(patchesPoolDir):
        patchDir = os.path.join(patchesPoolDir, patchPoolId)
        if not os.path.isdir(patchDir):
            continue
        patchInfoFile = os.path.join(patchDir, 'patchInfo.txt')
        if not os.path.isfile(patchInfoFile):
            err('File not found: {}'.format(patchInfoFile))
            continue
        stmtInfoDict = readPatchInfoFile(stmtInfoDict, patchPoolId, patchInfoFile)
    return stmtInfoDict


def readPatchInfoFile(stmtInfoDict: dict, patchPoolId: str, infoFile: str):
    patchPoolId = int(patchPoolId)
    with open(infoFile, 'r') as file:
        for line in file:
            if line.startswith('stmtLocation: '):
                location = line.strip()[len('stmtLocation: '):]
            elif line.startswith('compilationTimeMs: '):
                compileTime = int(line.strip()[len('compilationTimeMs: '):])
    if location not in stmtInfoDict:
        stmtInfoDict[location] = {'patches': [patchPoolId], 'generationTime': compileTime}
    else:
        stmtInfoDict[location]['patches'].append(patchPoolId)
        stmtInfoDict[location]['generationTime'] = stmtInfoDict[location]['generationTime'] + compileTime
    return stmtInfoDict

def readPatchValidationInfo(pid: int, bid: int, stmtInfoDict: dict, validationLog: str):
    plausiblePatchPoolIds = []
    # curPatchPoolId = None
    with open(validationLog, 'r') as file:
        for line in file:
            # if line.startswith(">>Validating patchID:"):
            #     m = re.match(r'>>Validating patchID: \d+ \(patch directory name: (\d+)\)', line.strip())
            #     curPatchPoolId = int(m[1])
            if line.startswith('Time cost to validate patch'):
                m = re.match(r'Time cost to validate patch \d+ \(patch directory name: (\d+)\): (\d+) ms', line.strip())
                patchPoolId = int(m[1])
                validationTime = int(m[2])
                for location in stmtInfoDict:
                    if 'validationTime' not in stmtInfoDict[location]:
                        stmtInfoDict[location]['validationTime'] = {}
                    if patchPoolId in stmtInfoDict[location]['patches']:
                        stmtInfoDict[location]['validationTime'][patchPoolId] = validationTime
            elif line.startswith("Directory of plausible patches: "):
                tmp = line.strip()[33:-1]
                if len(tmp) == 0:
                    warn('{}_{} has no plausible patches'.format(pid, bid))
                    break
                else:
                    tmp = tmp.split(', ')
                    for id in tmp:
                        plausiblePatchPoolIds.append(int(id))
                    for location in stmtInfoDict:
                        if 'plausiblePatches' not in stmtInfoDict[location]:
                            stmtInfoDict[location]['plausiblePatches'] = []
                        for patchId in stmtInfoDict[location]['patches']:
                            if patchId in plausiblePatchPoolIds:
                                stmtInfoDict[location]['plausiblePatches'].append(patchId)
    return stmtInfoDict
    

# def parseStmtInfo(patchesInfo):
#     stmtInfoDict = {}
#     for stmtDict in patchesInfo:
#         location = stmtDict['stmtLocation']
#         parseTime = getDictIntValue(stmtDict, 'parseSuspCodeNodeTimeMs')
#         genTime = getDictIntValue(stmtDict, 'patchesGenerationTimeMs')
#         compilablePatches = []  # only record the patch-pool ids of patches that are compilable
#         totalPatchCompilationTime = 0
#         cantCompilePatchesNum = 0
#         if 'patches' in stmtDict:
#             for patchDict in stmtDict['patches']:
#                 if 'patchPoolId' in patchDict:
#                     compilablePatches.append(patchDict['patchPoolId'])
#                 if 'compilable' not in patchDict or patchDict['compilable'] == False:
#                     cantCompilePatchesNum += 1
#                 totalPatchCompilationTime += patchDict['compilationTimeMs']
#         stmtProcessTime = parseTime + genTime + totalPatchCompilationTime
#         stmtInfoDict[location] = {'patches': compilablePatches, 'generationTime': stmtProcessTime}
#     return stmtInfoDict

def getDictIntValue(dic, key):
    return dic[key] if key in dic else 0


def err(msg: str):
    print('[ERROR]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def warn(msg: str):
    print('[WARNING]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def log(msg: str):
    print('[INFO]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

if __name__ == '__main__':
    # readPatchGenInfo()
    main()
        
