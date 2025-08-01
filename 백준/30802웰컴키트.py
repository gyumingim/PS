'''
이거 왤캐 이해가 어렵나
'''

from math import ceil


N = int(input())
lst = list(map(int, input().split()))
answer = 0
T, P = map(int, input().split())

for l in lst:
   answer += ceil(l / T)        

print(answer)
print(N//P, N%P)