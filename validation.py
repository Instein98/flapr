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

def validateAll(patchesDir:str, d4jMvnProjDir:str, outputDir:str, restartJVM=False):
    for pid in projDict.keys():
        bidList, depList = projDict[pid]
        for bid in bidList:
            if bid in depList:
                continue
            doValidate(pid, bid, os.path.join(patchesDir, '{}_{}'.format(pid, bid), 'patches-pool'), 
                            os.path.join(d4jMvnProjDir, pid, str(bid)), os.path.abspath(outputDir), restartJVM=restartJVM)

def validateSample(patchesDir:str, d4jMvnProjDir:str, outputDir:str, k:int, restartJVM=False):  # randomly do patches validation for k projects of each pid
    for pid in projDict.keys():
        bidList, depList = projDict[pid]
        for depId in depList:
            bidList.remove(depId)
        selectedPidList = random.sample(bidList, k)
        for bid in selectedPidList:
            doValidate(pid, bid, os.path.join(patchesDir, '{}_{}'.format(pid, bid), 'patches-pool'), 
                            os.path.join(d4jMvnProjDir, pid, str(bid)), os.path.abspath(outputDir), restartJVM=restartJVM)

def doValidate(pid:str, bid:int, patchesPoolPath:str, projPath:str, outputDir:str, restartJVM=False):
    print('\n')
    outputLogAbsPath = os.path.join(os.path.abspath(outputDir), '{}-{}.validation.log'.format(pid, bid))
    if os.path.isfile(outputLogAbsPath):
        with open(outputLogAbsPath) as log:
            if "BUILD SUCCESS" in log.read():
                print("{}-{} has been already validated, skipping".format(pid, bid))
                return
    print("================ Validating {}-{} ================".format(pid, bid))
    if not os.path.isdir(os.path.join(projPath, 'patches-pool')):
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


if __name__ == '__main__':
    validateAll(patchesDir, d4jMvnProjDir, outputDir, restartJVM=True)
    validateSample(patchesDir, d4jMvnProjDir, outputDir, 3)
    # print(outputDir)