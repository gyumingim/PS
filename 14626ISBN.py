N = input()

가중치 = 0
홀수 = False

for (index, i) in enumerate(N):
    if i == "*":
        if index%2==0:
            continue
        else:
            홀수 = True
            continue
    i = int(i)
    
    if index%2==0:
        가중치 += i
    else:
        가중치 += i * 3

if 홀수:
    for i in range(0, 10):
        if (가중치 + 3 * i)%10 == 0: 
            print(i)
            exit()
else:
    for i in range(0, 10):
        if (가중치 + i)%10 == 0: 
            print(i)
            exit()