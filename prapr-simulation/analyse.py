from pathlib import Path

reportDir = Path('simulateReport')

def readReports():
    result = {}
    for path in reportDir.glob('**/*-ideal.csv'):
        stem = path.stem
        bid = stem[:stem.index('-')]
        pid = path.parent.name
        bugId = pid + '-' + bid
        if bugId not in result:
            result[bugId] = [{}, {}]
        result[bugId][0] = readReport(path)  # 0 is ideal setting, 1 is worst setting
    for path in reportDir.glob('**/*-worst.csv'):
        stem = path.stem
        bid = stem[:stem.index('-')]
        pid = path.parent.name
        bugId = pid + '-' + bid
        if bugId not in result:
            result[bugId] = [{}, {}]
        result[bugId][1] = readReport(path)  # 0 is ideal setting, 1 is worst setting
    return result

def readReport(path: Path):
    res = {}
    with path.open(mode='r') as file:
        isFirstLine = True
        for line in file:
            if isFirstLine:
                columnNames = line.strip().split(', ')[1:]  # exclude the first 'FL' column
                res['columns'] = columnNames
                isFirstLine = False
                continue
            values = line.strip().split(', ')
            flName = values[0]
            data = values[1:]
            res[flName] = data
    return res

def find1(reportsData: dict):
    """
    Find the cases that better FL find the correct patch slower because of more not tied plausible patches are generated/validated before the correct patch.
    """
    pairCount = 0
    bugIdCount = 0
    for bugId in reportsData:
        found = False
        idealData = reportsData[bugId][0]
        worstData = reportsData[bugId][1]
        assert len(idealData['columns']) == len(worstData['columns'])
        assert '#PBeforeC' in idealData['columns']
        pbeforecIdx = idealData['columns'].index('#PBeforeC')
        assert '1stBugStmtEffRank' in idealData['columns']
        firstBuggyRankIdx = idealData['columns'].index('1stBugStmtEffRank')  # use effective rank
        assert 'TimeToFind1stC' in idealData['columns']
        timeToFindFirstCIdx = idealData['columns'].index('TimeToFind1stC')
        for fl1 in idealData:
            if fl1 == 'columns':
                continue
            for fl2 in idealData:
                if fl2 == 'columns' or fl1 == fl2:
                    continue
                if idealData[fl1][pbeforecIdx] == '-1' or idealData[fl1][pbeforecIdx] == 'ERROR' \
                    or idealData[fl2][pbeforecIdx] == '-1' or idealData[fl2][pbeforecIdx] == 'ERROR' \
                    or idealData[fl1][firstBuggyRankIdx] == '-1' or idealData[fl1][firstBuggyRankIdx] == 'ERROR' \
                    or idealData[fl2][firstBuggyRankIdx] == '-1' or idealData[fl2][firstBuggyRankIdx] == 'ERROR' \
                    or idealData[fl1][timeToFindFirstCIdx] == '-1' or idealData[fl1][timeToFindFirstCIdx] == 'ERROR' \
                    or idealData[fl2][timeToFindFirstCIdx] == '-1' or idealData[fl2][timeToFindFirstCIdx] == 'ERROR':
                        continue
                if int(idealData[fl1][pbeforecIdx]) < int(idealData[fl2][pbeforecIdx]) \
                    and int(worstData[fl1][pbeforecIdx]) < int(worstData[fl2][pbeforecIdx]) \
                    and int(idealData[fl1][firstBuggyRankIdx]) > int(idealData[fl2][firstBuggyRankIdx]) \
                    and int(idealData[fl1][timeToFindFirstCIdx]) < int(idealData[fl2][timeToFindFirstCIdx]) \
                    and int(worstData[fl1][timeToFindFirstCIdx]) < int(worstData[fl2][timeToFindFirstCIdx]):
                    print('Find 1: {} {}-{}'.format(bugId, fl1, fl2))
                    pairCount+=1
                    found = True
        if found:
            bugIdCount += 1
    print('(1) Found {} pairs among {} projects'.format(pairCount, bugIdCount))



def find2(reportsData: dict):
    """
    Find the cases that better FL finds the correct patch slower in the ideal case but not in the worst case because of the tied patches.
    """
    pairCount = 0
    bugIdCount = 0
    for bugId in reportsData:
        found = False
        idealData = reportsData[bugId][0]
        worstData = reportsData[bugId][1]
        assert len(idealData['columns']) == len(worstData['columns'])
        assert '1stBugStmtEffRank' in idealData['columns']
        firstBuggyRankIdx = idealData['columns'].index('1stBugStmtEffRank')  # use effective rank
        assert 'TimeToFind1stC' in idealData['columns']
        timeToFindFirstCIdx = idealData['columns'].index('TimeToFind1stC')
        for fl1 in idealData:
            if fl1 == 'columns':
                continue
            for fl2 in idealData:
                if fl2 == 'columns' or fl1 == fl2:
                    continue
                if idealData[fl1][firstBuggyRankIdx] == '-1' or idealData[fl1][firstBuggyRankIdx] == 'ERROR' \
                    or idealData[fl2][firstBuggyRankIdx] == '-1' or idealData[fl2][firstBuggyRankIdx] == 'ERROR' \
                    or idealData[fl1][timeToFindFirstCIdx] == '-1' or idealData[fl1][timeToFindFirstCIdx] == 'ERROR' \
                    or idealData[fl2][timeToFindFirstCIdx] == '-1' or idealData[fl2][timeToFindFirstCIdx] == 'ERROR':
                        continue
                if int(idealData[fl1][firstBuggyRankIdx]) > int(idealData[fl2][firstBuggyRankIdx]) \
                    and int(idealData[fl1][timeToFindFirstCIdx]) < int(idealData[fl2][timeToFindFirstCIdx]) \
                    and int(worstData[fl1][timeToFindFirstCIdx]) > int(worstData[fl2][timeToFindFirstCIdx]):
                    print('Find 2: {} {}-{}'.format(bugId, fl1, fl2))
                    pairCount+=1
                    found = True
        if found:
            bugIdCount += 1
    print('(2) Found {} pairs among {} projects'.format(pairCount, bugIdCount))


if __name__ == '__main__':
    reportsData = readReports()
    # print(reportsData)
    find1(reportsData)
    find2(reportsData)
