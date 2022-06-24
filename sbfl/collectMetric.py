"""
This script is to collect `totalfailed`, `totalpassed`, `failed(s)`, and `passed(s)` for each project or code element
"""

import os
import subprocess as sp

d4jMvnProjDir = '/home/yicheng/apr/d4jMvnForUniapr/d4jMvnProj/'
d4jProjCoverageDir = '/home/yicheng/apr/flapr/Coverage/Defects4j/'
allTestsFilesDir = '/home/yicheng/apr/d4jMvnForUniapr/all_tests_files/'

# format: fullyQualifiedClassName::testName
def getSetOfExpectedFailingTest(pid, bid):
    process = sp.Popen('defects4j info -p {} -b {}'.format(pid, bid),
                       shell=True, stderr=sp.PIPE, stdout=sp.PIPE, universal_newlines=True)
    stdout, _ = process.communicate()
    lines = stdout.strip().split('\n')
    start = False
    res = set()
    for line in lines:
        if 'Root cause in triggering tests:' in line:
            start = True
        elif '------------------------------------------------------' in line and start == True:
            start = False
            break
        elif line.startswith(' - ') and start == True:
            tmp = line[3:]
            res.add(tmp)
    return res

def getSetOfPassingFailingTests(pid, bid):
    allTestsSet = set()
    allTestsFilePath = os.path.join(allTestsFilesDir, pid, str(bid), 'all_tests')
    with open(allTestsFilePath) as file:
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
    testDir = sp.check_output("defects4j export -p dir.src.tests", shell=True, universal_newlines=True, cwd=projPath)
    return os.path.join(projPath, testDir)

def isTestClass(testSourcePath, dotClassName):
    slashClassName = dotClassName.replace('.', '/')
    if os.path.exists("{}/{}.java".format(testSourcePath, slashClassName)):
        return True
    else:
        return False

def processCoverageFile(pid: str, bid: int, covFilePath: str, passingTestSet: set, failingTestSet: set):
    # format: { codeElement: [passed(s), failed(s)] }
    resDict = {}
    projTestSourceDir = getTestSourceDirPath(pid, bid)
    with open(covFilePath, 'r') as file:
        for line in file:
            tmp = line.strip().split()
            curTest = tmp[0]
            curTest = curTest[:curTest.index('(')]
            curTest = curTest[:curTest.rindex('.')] + '::' + curTest[curTest.rindex('.')+1:]
            passing = True
            # if this test can't be found 
            if curTest not in passingTestSet and curTest not in failingTestSet:
                continue
            elif curTest in failingTestSet:
                passing = False
            codeElements = tmp[1:]
            for element in codeElements:
                eleClassName = element[:element.index(':')]
                # code elements in test classes should not be considered
                if isTestClass(projTestSourceDir, eleClassName):
                    continue
                if element not in resDict.keys():
                    resDict[element] = [0, 0]
                if passing == True:
                    resDict[element][0] += 1
                else:
                    resDict[element][1] += 1
    return resDict

def outputCodeElements(outputFilePath: str, elementDict: dict, totalPassedNum: int, totalFailedNum: int):
    res = 'CodeElement, passed(s), failed(s), totalpassed, totalfailed'
    for element in elementDict.keys():
        res += '{}, {}, {}, {}, {}\n'.format(element, elementDict[element][0], elementDict[element][1], totalPassedNum, totalFailedNum)
    with open(outputFilePath, 'w') as file:
        file.write(res)

if __name__ == '__main__':
    passingTestSet, failingTestSet = getSetOfPassingFailingTests('Chart', 4)
    resDict = processCoverageFile('Chart', 4, '/home/yicheng/apr/flapr/Coverage/Defects4j/Chart/4.txt', passingTestSet, failingTestSet)
    # print(resDict)
    outputCodeElements('tmp', resDict, len(passingTestSet), len(failingTestSet),)