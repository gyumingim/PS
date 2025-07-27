'''
에너지 모으기

이것도 브루트포스로 풀어보기
'''
answer = 0

def back_tracking(x):
    global answer

    if len(lst) <= 2:
        answer = max(x, answer)
        return 

    for i in range(1, len(lst)-1):
        target = lst[i - 1] * lst[i + 1] 

        v = lst.pop(i)
        back_tracking(x + target)
        lst.insert(i, v) 

N = int(input())
lst = list(map(int, input().split()))

back_tracking(0)

print(answer)