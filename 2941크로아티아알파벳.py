'''
단순 구현
'''

from sys import stdin
input = stdin.readline

lst = ['c=', 'c-', 'd-', 'lj', 'nj', 's=', 'z=']
lst2 = ['dz=']
A = input()[:-1]
leng = len(A)
idx = 0
cnt = 0
while idx < leng:

    if idx+3 <= leng and A[idx:idx+3] in lst2:
        idx += 3
        cnt += 1
        continue

    if idx+2 <= leng and A[idx:idx+2] in lst:
        idx += 2
        cnt += 1
        continue

    idx += 1
    cnt += 1
print(cnt)