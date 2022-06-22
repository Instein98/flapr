from operator import truediv
import os
import glob
import subprocess as sp
from pathlib import Path
from utils import iterateD4j120

covPath = "Coverage/Defects4j/"
d4jProjPath = "/home/yicheng/research/d4jProj/"

def getCwd(pid, bid):
    return "{}/{}_{}".format(d4jProjPath, pid, bid)

def getFailedTests(pid, bid):
    res = set()
    process = sp.Popen("defects4j export -p tests.trigger", shell=True, stderr=sp.PIPE, stdout=sp.PIPE, cwd=getCwd(pid, bid), universal_newlines=True)
    stdout, _ = process.communicate()
    for string in stdout.strip().split('\n'):
        tmp = string.split('::')
        res.add("{0}.{1}({0})".format(tmp[0], tmp[1]))
    # print(res)
    if not res:
        print("[ERROR] Failed to ge the failed tests list for {}-{}".format(pid, bid))
    return res

def getTestSourceDirPath(pid, bid):
    projPath = getCwd(pid, bid)
    testDir = sp.check_output("defects4j export -p dir.src.tests", shell=True, universal_newlines=True, cwd=projPath)
    return "{}/{}".format(projPath, testDir)

def isTestClassPath(testSourcePath, dotClassName):
    slashClassName = dotClassName.replace('.', '/')
    if os.path.exists("{}/{}.java".format(testSourcePath, slashClassName)):
        return True
    else:
        return False

def collectStmtCoveredByFailedTests(pid, bid):
    if os.path.exists("SuspiciousCodePositions/{}_{}/Covered.txt".format(pid, bid)):
        print("{}_{}/Covered.txt already exists, skip".format(pid, bid))
        return
    print("Generating {}_{}/Covered.txt".format(pid, bid))
    res = set()
    failedTestSet = getFailedTests(pid, bid)
    covLogPath = "{}/{}/{}.txt".format(covPath, pid, bid)
    if not os.path.exists(covLogPath):
        print("[WARNING] {} does not exist, skip".format(covLogPath))
        return
    testSourcePath = getTestSourceDirPath(pid, bid)
    with open(covLogPath) as log:
        for line in log:
            tmp = line.strip().split()
            if tmp[0] in failedTestSet:
                for location in tmp[1:]:
                    classPath = location[:location.index(':')]
                    if isTestClassPath(testSourcePath, classPath):
                        continue
                    lineNum = location[location.rindex(':')+1:]
                    res.add('{}@{}'.format(classPath, lineNum))
    Path("SuspiciousCodePositions/{}_{}".format(pid, bid)).mkdir(parents=True, exist_ok=True)
    with open("SuspiciousCodePositions/{}_{}/Covered.txt".format(pid, bid), 'w') as file:
        for location in res:
            file.write(location + "\n")

if __name__ == '__main__':
    # getFailedTests('Chart', 4)
    # collectStmtCoveredByFailedTests('Chart', 1)
    # print(isTestClassPath('Chart', '1', 'org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests'))
    iterateD4j120(collectStmtCoveredByFailedTests)