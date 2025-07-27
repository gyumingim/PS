'''
에너지 모으기

이것도 브루트포스로 풀어보기
'''
from copy import deepcopy


max_ = 0

def foo(templst, i, result):
    global max_

    if len(templst)<=2:
        max_ = max(result, max_)
        return 

    templst.pop(i)
    result += templst[i-1] * templst[i]

    for j in range(1, len(templst)-1):
        foo(deepcopy(templst), j, result)

    if len(templst)<=2:
        max_ = max(result, max_)
        return 

    

N = int(input())
lst = list(map(int, input().split()))
templst = deepcopy(lst)
result = 0

for i in range(1, len(deepcopy(templst))-1):
    foo(deepcopy(templst), i, 0)

print(max_)