import os
import glob
import subprocess as sp
from pathlib import Path
from utils import iterateD4j120

covPath = "Coverage/Defects4j/"
d4jProjPath = "/home/yicheng/research/d4jProj/"

def getFailedTests(pid, bid):
    res = set()
    process = sp.Popen("defects4j export -p tests.trigger", shell=True, stderr=sp.PIPE, stdout=sp.PIPE, cwd="{}/{}/{}".format(d4jProjPath, pid, bid), universal_newlines=True)
    stdout, stderr = process.communicate()
    for string in stdout.strip().split('\n'):
        tmp = string.split('::')
        res.add("{0}.{1}({0})".format(tmp[0], tmp[1]))
    # print(res)
    if not res:
        print("[ERROR] Failed to ge the failed tests list for {}-{}".format(pid, bid))
    return res

def collectStmtCoveredByFailedTests(pid, bid):
    # for projPath in glob.glob(covPath + '/*'):
    #     pid = os.path.basename(os.path.normpath(projPath))
    #     for covLog in glob.glob(projPath + '/*'):
    #         bid = os.path.basename(covLog)[:-4]
    #         # print("{}-{}".format(pid, bid))
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
    with open(covLogPath) as log:
        for line in log:
            tmp = line.strip().split()
            if tmp[0] in failedTestSet:
                for location in tmp[1:]:
                    classPath = location[:location.index(':')]
                    lineNum = location[location.rindex(':')+1:]
                    res.add('{}@{}'.format(classPath, lineNum))
    Path("SuspiciousCodePositions/{}_{}".format(pid, bid)).mkdir(parents=True, exist_ok=True)
    with open("SuspiciousCodePositions/{}_{}/Covered.txt".format(pid, bid), 'w') as file:
        for location in res:
            file.write(location + "\n")

if __name__ == '__main__':
    # print('yes')
    # getFailedTests('Chart', 4)
    # collectStmtCoveredByFailedTests('Chart', 1)
    iterateD4j120(collectStmtCoveredByFailedTests)