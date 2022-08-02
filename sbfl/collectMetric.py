"""
This script is to collect `totalfailed`, `totalpassed`, `failed(s)`, and `passed(s)` for each project or code element
This script is using the coverage collected during execution of `defects4j test` by TestCovAgent
"""

import os
import subprocess as sp
from pathlib import Path

d4jMvnProjDir = '/home/yicheng/research/apr/d4jMvnForUniapr/d4jMvnProj'
d4jProjCoverageDir = '/home/yicheng/research/apr/testCovAgent/d4jCov/covResult'
outputDir = 'sbflExeInfo'

# format: fullyQualifiedClassName::testName
def getSetOfExpectedFailingTest(pid, bid):
    res = set()
    expectedFTFile = os.path.join(d4jProjCoverageDir, pid, bid, 'expected_failing_tests')
    with open(expectedFTFile, 'r') as file:
        for line in file:
            res.add(line.strip())
    return res

def getSetOfPassingFailingTests(pid, bid, allTestsFilePath):
    allTestsSet = set()
    with open(allTestsFilePath, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                idx = line.index('(')
                testName = line[:idx]
                className = line[idx+1:-1]
                allTestsSet.add('{}::{}'.format(className, testName))
    print('allTestsSet size: {}'.format(len(allTestsSet)))
    failingTestsSet = getSetOfExpectedFailingTest(pid, bid)
    print('failingTestsSet size: {}'.format(len(failingTestsSet)))
    passingTestsSet = allTestsSet - failingTestsSet
    print('passingTestsSet size: {}'.format(len(passingTestsSet)))
    assert len(passingTestsSet) == len(allTestsSet) - len(failingTestsSet)
    return passingTestsSet, failingTestsSet
    
def getTestSourceDirPath(pid: str, bid: int):
    projPath = os.path.join(d4jMvnProjDir, pid, str(bid))
    testDir = sp.check_output("defects4j export -p dir.src.tests", shell=True, universal_newlines=True, cwd=projPath, stderr=sp.DEVNULL)
    return os.path.join(projPath, testDir)

def isTestClass(testSourcePath, dotClassName):
    slashClassName = dotClassName.replace('.', '/')
    if os.path.exists("{}/{}.java".format(testSourcePath, slashClassName)):
        return True
    else:
        return False

def readCovFile(filePath):
    idxDict = {}
    testDict = {}  # testClass -> {testMethod -> list of idx}
    with open(filePath, 'r') as file:
        for line in file:
            if '->' in line:
                tmp = line.strip().split(' -> ')
                idx = tmp[0]
                element = tmp[1]
                firstColonIdx = element.index(':')
                lastColonIdx = element.rindex(':')
                dotClassName = element[:firstColonIdx].replace("/", ".")
                lineNum = element[lastColonIdx+1:]
                newEleStr = dotClassName + ":" + lineNum
                idxDict[idx] = newEleStr
            elif ',' in line:
                tmp = line.strip().split(', ')
                testName = tmp[0]
                testDotClassName = testName[:testName.index('#')].replace("/", ".")
                testMethodName = testName[testName.index('#')+1:]
                idxList = []
                for idx in tmp[1:]:
                    idxList.append(idx)
                if testDotClassName not in testDict:
                    testDict[testDotClassName] = {}
                    testDict[testDotClassName][testMethodName] = idxList
                else:
                    testDict[testDotClassName][testMethodName] = idxList
    return idxDict, testDict


def processCoverageFile(pid: str, bid: str, covFilePath: str, passingTestSet: set, failingTestSet: set):
    # format: { codeElement: [set of passing tests covering it, set of failing tests covering it] }
    resDict = {}
    projTestSourceDir = getTestSourceDirPath(pid, bid)
    idxDict, testDict = readCovFile(covFilePath)

    for testClass in testDict:
        for testMethod in testDict[testClass]:
            curTest = testClass + '::' + testMethod
            passing = True
            # if this test can't be found 
            if curTest not in passingTestSet and curTest not in failingTestSet:
                continue
            elif curTest in failingTestSet:
                passing = False
            for idx in testDict[testClass][testMethod]:
                element = idxDict[idx]
                eleClassName = element[:element.index(':')]
                # code elements in test classes should not be considered
                if isTestClass(projTestSourceDir, eleClassName):
                    continue
                if element not in resDict.keys():
                    resDict[element] = [set(), set()]
                if passing == True:
                    resDict[element][0].add(curTest)
                else:
                    resDict[element][1].add(curTest)
    return resDict


def outputCodeElements(outputFilePath: str, elementDict: dict, totalPassedNum: int, totalFailedNum: int, verbose=False):
    """ if verbose, tests covering the code elements will be printed, otherwise only number of such tests will be shown """
    if os.path.isfile(outputFilePath):
        print("skipping {}".format(outputFilePath))
        return
    res = 'CodeElement, passed(s), failed(s), totalpassed, totalfailed\n'
    for element in elementDict.keys():
        res += '{}, {}, {}, {}, {}\n'.format(
            element, 
            elementDict[element][0] if verbose else len(elementDict[element][0]), 
            elementDict[element][1] if verbose else len(elementDict[element][1]), 
            totalPassedNum, 
            totalFailedNum)
    # create parent dirs if not exist
    Path(outputFilePath).parent.mkdir(parents=True, exist_ok=True)
    with open(outputFilePath, 'w') as file:
        file.write(res)

def main():
    for pid in os.listdir(d4jProjCoverageDir):
        pidPath = os.path.join(d4jProjCoverageDir, pid)
        if not os.path.isdir(pidPath):
            continue
        for bid in os.listdir(pidPath):
            bidPath = os.path.join(pidPath, bid)
            if not os.path.isdir(bidPath):
                continue
            covLogPath = os.path.join(bidPath, 'coverage.txt')
            outputPath = os.path.join(outputDir, pid, '{}.csv'.format(bid))
            if os.path.isfile(outputPath):
                print("skipping {}".format(outputPath))
                continue
            allTestsFilePath = os.path.join(bidPath, 'all_tests')
            if not os.path.isfile(allTestsFilePath):
                print('[WARNING] all_tests file not found: {}. Is {}-{} deprecated?'.format(allTestsFilePath, pid, bid))
                continue

            # Start analysis
            print("\n=============== processing {}-{} ===============".format(pid, bid))
            passingTestSet, failingTestSet = getSetOfPassingFailingTests(pid, bid, allTestsFilePath)
            resDict = processCoverageFile(pid, bid, covLogPath, passingTestSet, failingTestSet)
            outputCodeElements(outputPath, resDict, len(passingTestSet), len(failingTestSet), verbose=False)
            

if __name__ == '__main__':
    # passingTestSet, failingTestSet = getSetOfPassingFailingTests('Chart', 4)
    # resDict = processCoverageFile('Chart', 4, '/home/yicheng/apr/flapr/Coverage/Defects4j/Chart/4.txt', passingTestSet, failingTestSet)
    # print(resDict)
    # outputCodeElements('tmp', resDict, len(passingTestSet), len(failingTestSet), verbose=False)
    main()