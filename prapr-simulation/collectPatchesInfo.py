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
        index = mutation.findtext('index')
        block = mutation.findtext('block')
        description = mutation.findtext('description')
        mutator = mutation.findtext('mutator')
        if '.' in mutator:
            mutator = mutator[mutator.rindex('.')+1:]
        validationTime = int(mutation.findtext('patchExecutionTime')[:-2])
        # print(mutationDotClassName + ':' + lineNum + '@' + mutator + '@' + str(validationTime))
        location = mutationDotClassName + ':' + lineNum
        # patchId = location + '@' + mutator
        if location not in stmtInfoDict:
            stmtInfoDict[location] = []  # list of patches
        stmtInfoDict[location].append(
            {'mutatedClass': mutationDotClassName, 
            'lineNumber': lineNum, 'index': index, 
            'block': block, 'description': description, 
            'mutator': mutator, 'validationTime': validationTime, 
            'isPlausible': att['status'] == 'SURVIVED', 
            'isCorrect': False}
        )
    return stmtInfoDict

def readPatchCorrectnessInfo(pid: str, bid: str, stmtInfoDict: dict):
    patchesDir = os.path.join(praprPatchCorrectnessDir, pid, bid)

    if not os.path.isdir(patchesDir):
        log('No plausible patches found for {}-{} in correctness data'.format(pid, bid))
        return stmtInfoDict

    log('----- Reading correctness information of {}-{} -----'.format(pid, bid))
    for patchDir in os.listdir(patchesDir):
        patchDirPath = os.path.join(patchesDir, patchDir)
        if not os.path.isdir(patchDirPath):
            continue
        # only use the correct patch information of the correctness data
        correctFilePath = os.path.join(patchDirPath, 'correct')
        if not os.path.isfile(correctFilePath):
            continue

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
                elif 'Description: ' in line:
                    description = line.strip()[len('Description: '):]

        location = dotClassName + ':' + lineNum
        if location not in stmtInfoDict:
            warn('{}-{} data mismatch: location {} not in keys of stmtInfoDict'.format(pid, bid, location))
            inconsistentProj.add('{}-{}'.format(pid, bid))
            continue
        else:
            patchList = stmtInfoDict[location]
            foundCorrespondingPatch = False
            for patch in patchList:
                if patch['mutatedClass'] == dotClassName  \
                        and patch['lineNumber'] == lineNum  \
                        and patch['mutator'] == mutator  \
                        and patch['description'] == description:
                    foundCorrespondingPatch = True
                    patch['isPlausible'] = True  # Found some patches not survive in timing data but marked as correct in correctness data
                    patch['isCorrect'] = True
                    break
            if not foundCorrespondingPatch:
                warn('{}-{} data mismatch: correct patch {}@{}@{}@{} not found in timing data'.format(pid, bid, dotClassName, lineNum, mutator, description))
                inconsistentProj.add('{}-{}'.format(pid, bid))
            else:
                log('{}-{}: correct patch {}@{}@{}@{} successfully found'.format(pid, bid, dotClassName, lineNum, mutator, description))
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
