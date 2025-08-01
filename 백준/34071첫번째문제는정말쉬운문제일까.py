from sys import stdin
input = stdin.readline

N = int(input())
lst = []
for i in range(N):
    lst.append(int(input()))

if max(lst) == lst[0]:
    print('hard')
elif min(lst) == lst[0]:
    print('ez')
else:
    print('?')