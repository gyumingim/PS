'''
111
123
135
147
159

234
246
258

345
357
369

456
468

567
579

678

789

'''

from sys import stdin
input = stdin.readline

lst = [123, 135, 147, 159, 234, 246, 258, 345, 357, 369, 456, 468, 567, 579, 678, 789]
non_lst = [111, 222, 333, 444, 555, 666, 777, 888, 999, 210, 420, 630, 840]
cnt = 0

A = int(input()[:-1])
if A >= 100:
    for i in lst:
        if A >= i:
            cnt += 1
        if A >= int(str(i)[::-1]):
            cnt += 1
    for i in non_lst:
        if A >= i:
            cnt += 1
    print(cnt + 99)
else:
    print(A)