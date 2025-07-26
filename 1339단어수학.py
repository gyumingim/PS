'''
다 때려박으면 안되나??

해봐야지

큰 자리수에 큰 수를 대입하는건 안되는 방법임, 모든 경우의 수?

글자수 만큼 모든 경우의 수를 대입하는 방법?
'''
from copy import deepcopy

try:

    N = int(input())
    lst = []

    dic = {chr(c): -1 for c in range(ord("A"), ord("Z") + 1)}  # A~Z 모두 -1로 초기화


    for _ in range(N):
        lst.append(input())

    temp_lst = deepcopy(lst)

    i = 9
    while i > 0:
        lst = sorted(lst, key=len, reverse=True)
        
        if "".join(lst) == "":
            break

        if dic[lst[0][0]] == -1:
            dic[lst[0][0]] = i
            lst[0] = lst[0][1:]
            i -= 1
        else:
            lst[0] = lst[0][1:]


    sum_ = 0

    for l in temp_lst:
        num = ""
        for letter in l:
            num += str(dic[letter])
        
        sum_ += int(num)

    print(sum_)

        
        

except Exception:
    print("dd")