"""
This script is to collect `totalfailed`, `totalpassed`, `failed(s)`, and `passed(s)` for each project or code element
"""

import os
import subprocess as sp

d4jProjCoverageDir = 'xxx'
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
    
def processCoverageFile(covFilePath: str):
    # format: { codeElement: [passed(s), failed(s)] }
    resDict = {}
    with open(covFilePath, 'r') as file:
        for line in file:
            pass

if __name__ == '__main__':
    getSetOfPassingFailingTests('Chart', 4)