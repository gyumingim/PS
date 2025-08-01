"""
세로

짝 -> 홀 2
홀 -> 짝 6, 22, 6, 

가로

짝 -> 홀 1
홀 -> 짝 3, 11, 3, 

세로, 가로

1사분면, 2사분면, 3사분면, 4사분면을 나눠서 해야함

"""

N, R, C = map(int, input().split())

max_num = 2**(2*N)
answer = 0

# 한 변의 길이를 찾아야함
line = 2**N

while line != 1:
    # 3 혹은 4사분면
    if R+1 > line/2:
        # 4사분면
        if C+1 > line/2:
            answer += max_num * (3/4)
            R -= line/2
            C -= line/2
        # 3사분면
        else:
            answer += max_num * (2/4)
            R -= line/2

    # 1 혹은 2사분면
    else:
        # 1사분면
        if C+1 > line/2:
            answer += max_num * (1/4)
            C -= line/2
        # 2사분면
        else:
            answer += max_num * (0)
    line /= 2
    max_num /= 4
print(int(answer))
