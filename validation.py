import os
import shutil
import random
import subprocess as sp


# v1.2.0: Closure 1-133, v2.0.0: Closure 1-176
# pid: (bid range, deprecated list)
projDict = {
    'Chart': (list(range(1, 27)), []),
    # 'Closure': (list(range(1, 134)), [63, 93]),  # have no patches for Closure for now
    'Lang': (list(range(1, 66)), [2]),
    'Math': (list(range(1, 107)), []),
    'Mockito': (list(range(1, 39)), []),
    'Time': (list(range(1, 28)), [21])
}

d4jMvnProjDir = '/home/yicheng/research/apr/d4jMvnForUniapr/d4jMvnProj/'
patchesDir = '/home/yicheng/research/apr/experiments/tbar/patches/'
outputDir = os.path.abspath('validationResult')
d4jProjPath = '/home/yicheng/research/apr/d4jProj'

def validateAll(restartJVM=False):
    for pid in projDict.keys():
        bidList, depList = projDict[pid]
        for bid in bidList:
            if bid in depList:
                continue
            doValidate(pid, bid, restartJVM=restartJVM)

def validateSample(k:int, restartJVM=False):  # randomly do patches validation for k projects of each pid
    for pid in projDict.keys():
        bidList, depList = projDict[pid]
        for depId in depList:
            bidList.remove(depId)
        selectedPidList = random.sample(bidList, k)
        for bid in selectedPidList:
            doValidate(pid, bid, restartJVM=restartJVM)

def doValidate(pid:str, bid:int, restartJVM=False):
    print('\n')
    patchesPoolPath = os.path.join(patchesDir, '{}_{}'.format(pid, bid), 'patches-pool')
    projPath = os.path.join(d4jMvnProjDir, pid, str(bid))
    outputLogAbsPath = os.path.join(os.path.abspath(outputDir), '{}-{}.validation.log'.format(pid, bid))
    if os.path.isfile(outputLogAbsPath):
        with open(outputLogAbsPath) as log:
            if "BUILD SUCCESS" in log.read():
                print("{}-{} has been already validated, skipping".format(pid, bid))
                return
    print("================ Validating {}-{} ================".format(pid, bid))
    if not os.path.isdir(os.path.join(projPath, 'patches-pool')):
        if not os.path.isdir(patchesPoolPath):
            print("{} does not exist!".format(patchesPoolPath))
            return
        shutil.copytree(patchesPoolPath, os.path.join(projPath, 'patches-pool'))
    if not os.path.isdir(os.path.abspath(outputDir)):
        os.makedirs(os.path.abspath(outputDir), exist_ok=True)
    process = sp.Popen("mvn org.uniapr:uniapr-plugin:1.0-SNAPSHOT:validate -DrestartJVM={} -Dd4jAllTestsFile=all_tests -Ddebug=false -l {}"
                .format('false' if restartJVM == False else 'true', outputLogAbsPath),
                cwd=projPath, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    exitCode = process.poll()
    shutil.rmtree(os.path.join(projPath, 'patches-pool'))
    if exitCode != 0:
        print('[ERROR] Uniapr exited with non-zero exit code!')
        print(stdout)
        print(stderr)

# def doValidateWithD4j(pid:str, bid:int, patchesPoolPath:str, outputDir:str):
#     projPath = os.path.join(d4jProjPath, pid, bid)
#     # backup failing tests
#     failingTestFilePath = os.path.join(projPath, 'failing_tests')
#     if not os.path.isfile(failingTestFilePath + '.bak'):
#         shutil.copy(failingTestFilePath, os.path.isfile(failingTestFilePath + '.bak'))
#     # start patch validation
#     for idx in os.listdir(patchesPoolPath):


if __name__ == '__main__':
    validateAll(restartJVM=True)
    # validateSample(3)
    # print(outputDir)

    # pid = 'Chart'
    # bid = 4
    # doValidate(pid, bid, os.path.join(patchesDir, '{}_{}'.format(pid, bid), 'patches-pool'), 
    #                         os.path.join(d4jMvnProjDir, pid, str(bid)), os.path.abspath(outputDir), restartJVM=True)

    # pid = 'Chart'
    # bidList = [7, 8, 9, 11, 18, 20, 24]
    # for bid in bidList:
    #     doValidate(pid, bid, restartJVM=True)