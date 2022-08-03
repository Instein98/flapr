import os
import json
from datetime import datetime
import xml.etree.ElementTree as et

praprTimingDir = '/home/yicheng/research/apr/apr-timing/prapr-timing/'
praprPatchCorrectnessDir = '/home/yicheng/research/apr/apr-timing/prapr_src_patches_1.2'
patchesInfoOutputDir = 'praprPatchesInfo'

inconsistentProj = set()

def readPatchesTimingInfo(xmlFilePath: str):
    stmtInfoDict = {}
    assert os.path.isfile(xmlFilePath)
    tree = et.parse(xmlFilePath)
    root = tree.getroot()
    log('----- Parsing {} -----'.format(xmlFilePath))
    for mutation in root:
        att = mutation.attrib
        # att['status']
        mutationDotClassName = mutation.findtext('mutatedClass')
        lineNum = mutation.findtext('lineNumber')
        mutator = mutation.findtext('mutator')
        if '.' in mutator:
            mutator = mutator[mutator.rindex('.')+1:]
        validationTime = int(mutation.findtext('patchExecutionTime')[:-2])
        # print(mutationDotClassName + ':' + lineNum + '@' + mutator + '@' + str(validationTime))
        location = mutationDotClassName + ':' + lineNum
        # patchId = location + '@' + mutator
        if location not in stmtInfoDict:
            stmtInfoDict[location] = {'patches': [], 'plausiblePatches': [], 'correctPatches': [], 'patchValidationTime': {}}
        stmtInfoDict[location]['patches'].append(mutator)
        stmtInfoDict[location]['patchValidationTime'][mutator] = validationTime
        if att['status'] == 'SURVIVED':
            stmtInfoDict[location]['plausiblePatches'].append(mutator)
    return stmtInfoDict

def readPatchCorrectnessInfo(pid: str, bid: str, stmtInfoDict: dict):
    plausibleDict = {}  # location:  list of mutator
    patchesDir = os.path.join(praprPatchCorrectnessDir, pid, bid)

    if not os.path.isdir(patchesDir):
        log('No plausible patches found for {}-{} in correctness data'.format(pid, bid))
        # Assuming the patch correctness data is more reliable than the timing data, remove the plausible patches found in the timing data
        for location in stmtInfoDict:
            for mutator in stmtInfoDict[location]['plausiblePatches']:
                stmtInfoDict[location]['plausiblePatches'].remove(mutator)
        return stmtInfoDict

    log('----- Reading correctness information of {}-{} -----'.format(pid, bid))
    for patchDir in os.listdir(patchesDir):
        patchDirPath = os.path.join(patchesDir, patchDir)
        if not os.path.isdir(patchDirPath):
            continue
        isCorrect = False
        infoFilePath = os.path.join(patchDirPath, 'mutant-info.log')
        assert os.path.isfile(infoFilePath)
        with open(infoFilePath, 'r') as file:
            for line in file:
                if 'Mutator: ' in line:
                    mutator = line.strip()[len('Mutator: '):]
                elif 'File Name: ' in line:
                    slashClassName = line.strip()[len('File Name: '):-5]
                    dotClassName = slashClassName.replace('/', '.')
                elif 'Line Number: ' in line:
                    lineNum = line.strip()[len('Line Number: '):]
        location = dotClassName + ':' + lineNum
        if location not in plausibleDict:
            plausibleDict[location] = []
        plausibleDict[location].append(mutator)
        correctFilePath = os.path.join(patchDirPath, 'correct')
        if os.path.isfile(correctFilePath):
            isCorrect = True

        if location not in stmtInfoDict:
            warn('{}-{} data mismatch: location {} not in keys of stmtInfoDict'.format(pid, bid, location))
            inconsistentProj.add('{}-{}'.format(pid, bid))
            continue
        else:
            mutatorList = stmtInfoDict[location]['patches']
            plausibleMutatorList = stmtInfoDict[location]['plausiblePatches']
            if mutator not in mutatorList:
                warn('{}-{} data mismatch: mutator {} does not exist for location {} in timing data'.format(pid, bid, mutator, location))
                inconsistentProj.add('{}-{}'.format(pid, bid))
                continue
            if mutator not in plausibleMutatorList:
                warn('{}-{} data mismatch: mutant {} is not plausible in timing data'.format(pid, bid, location + '@' + mutator))
                inconsistentProj.add('{}-{}'.format(pid, bid))
                continue
            if isCorrect:
                stmtInfoDict[location]['correctPatches'].append(mutator)
    
    # Assuming the patch correctness data is more reliable than the timing data, remove the plausible patches that are in timing data but not in correctness data.
    for location in plausibleDict:
        if location not in stmtInfoDict:
            continue  # should already warn
        for mutator in stmtInfoDict[location]['plausiblePatches']:
            if mutator not in plausibleDict[location]:
                stmtInfoDict[location]['plausiblePatches'].remove(mutator)
            
    return stmtInfoDict

def err(msg: str):
    print('[ERROR]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def warn(msg: str):
    print('[WARNING]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def log(msg: str):
    print('[INFO]({}) {}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), msg))

def main():
    for pid in os.listdir(praprTimingDir):
        if pid == 'Mockito-depreciated':
            continue
        pidPath = os.path.join(praprTimingDir, pid)
        if not os.path.isdir(pidPath):
            continue
        os.makedirs(os.path.join(patchesInfoOutputDir, pid), exist_ok=True)
        for xmlFile in os.listdir(pidPath):
            if not xmlFile.endswith('.xml'):
                continue
            bid = xmlFile[:-4]
            xmlFilePath = os.path.join(pidPath, xmlFile)
            print()
            log('===== Processing {}-{} ====='.format(pid, bid))
            stmtInfoDict = readPatchesTimingInfo(xmlFilePath)
            stmtInfoDict = readPatchCorrectnessInfo(pid, bid, stmtInfoDict)
            j = json.dumps(stmtInfoDict, indent=2)
            with open(os.path.join(patchesInfoOutputDir, pid, bid + '.json'), 'w') as file:
                print(j, file=file)

    # print the projects have inconsistent data in timing data and correctness data
    print('inconsistent projects: {}'.format(inconsistentProj))

if __name__ == '__main__':
    main()
