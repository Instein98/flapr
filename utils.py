
# D4J v1.2.0
def iterateD4j120(fun):
    pidList = ["Chart", "Lang", "Math", "Time", "Mockito", "Closure"]
    for pid in pidList:
        if pid == "Chart":
            for i in range(1, 27):
                fun(pid, i)
        elif pid == "Lang":
            deprecated = [2]
            for i in range(1, 66):
                if i not in deprecated:
                    fun(pid, i)
        elif pid == "Math":
            for i in range(1, 107):
                fun(pid, i)
        elif pid == "Time":
            deprecated = [21]
            for i in range(1, 28):
                if i not in deprecated:
                    fun(pid, i)
        elif pid == "Mockito":
            for i in range(1, 39):
                fun(pid, i)
        elif pid == "Closure":
            deprecated = [63, 93]
            for i in range(1, 134):
                if i not in deprecated:
                    fun(pid, i)