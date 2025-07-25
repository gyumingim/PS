'''

'''

from sys import stdin
input = stdin.readline

cnt = 0
N = int(input())


def cert(lst):
    global cnt
    if len(lst) == N:
        cnt += 1
        return

    for i in range(N):
        hasBreak = False
        if i in lst:
            continue
        for (idx, l) in enumerate(lst):
            if i == l + len(lst) - idx:
                hasBreak = True
                break
            if i == l - len(lst) + idx:
                hasBreak = True
                break
        if hasBreak:
            continue

        cert(lst + [i])

cert([])

print(cnt)



