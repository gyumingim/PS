'''
2차원 배열이라 보기 어려웠음, 그냥 1차원 배열로 풀고

백트래킹 하지도 못했는데.. ㅠㅠ

index는 0부터
'''

# direction은 0부터
from copy import deepcopy


direction = [
    -4,
    -5,
    -1,
     3,
     4,
     5,
     1,
    -3
]

lst = [
    [0, 0],
    [0, 0],
    [0, 0],
    [0, 0],
    
    [0, 0],
    [0, 0],
    [0, 0],
    [0, 0],
    
    [0, 0],
    [0, 0],
    [0, 0],
    [0, 0],
    
    [0, 0],
    [0, 0],
    [0, 0],
    [0, 0],
    
]
answer = 0
for w in range(4):
    temp = list(map(int, input().split()))
    for i in range(0,8,2):
        lst[temp[i]-1] = [i+w*4, temp[i+1]]
        # 0, 0은 미리 먹기
        if w == 0 and i == 0:
            answer += temp[i]
            d = temp[i+1]
            # index니까 -1
            lst[temp[i]-1] = None

print(lst)

# 백트랙킹 시작 
# 1차원 배열이라 접근할 때, y에 *4 해주면 됨
def back_tracking(x, d, max_):
    global lst
    global answer
    breakpoint()
    # 초기화를 위한 deepcopy
    temp_lst = deepcopy(lst)

    # 물고기 이동시키기
    for i in range(16):
        # 보정값 to_direction
        correction = 0
        try:
            to_direction = direction[lst[i][1]-1 + correction]
        except Exception:
            continue
        for _ in range(8):
            # 그쪽으로 갈 수 있는가?
            # 갈 수 있다면
            if (0 <= (lst[i][0] + to_direction)) and ((lst[i][0] + to_direction) <= 15) and lst[lst[i][0] + to_direction] != None:
                # 교체
                lst[i][0] = 
                break
            # 갈 수 없다면
            else: 
                # 45도 회전
                correction -= 1
                to_direction = direction[lst[i][1] - 1 + correction]

    moved = False
    # 상어가 움직일 위치 정하기
    while 0 <= x + direction[d-1] and x + direction[d-1] <= 15:
        back_tracking(x + direction[d-1], direction[d-1], max_)
        lst = temp_lst
        x += direction[d-1]
        moved = True

    # 만약 한 곳도 못정했다면, 최댓값과 비교해서 큰 값 넣기
    if not moved:
        answer = max(answer, max_)

    


# 확정 먹방은 여기에~
# 여기 수정해야함

back_tracking(0, d, answer)

print(answer)