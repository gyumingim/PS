
# ↑, ↖, ←, ↙, ↓, ↘, →, ↗
# y, x
from copy import deepcopy


direction = [
    [ 1, 0],
    [ 1,-1],
    [ 0,-1],
    [-1,-1],
    [-1, 0],
    [-1, 1],
    [ 0, 1],
    [ 1, 1],
]

# 입력
lst = []
for _ in range(4):
    data = list(map(int, input().split()))  # 8개 숫자 (물고기, 방향)*4
    lst.append([[data[i], data[i + 1]] for i in range(0, 8, 2)])


# 백트랙킹
def back_tracking(y, x):
    # 그 자리 물고기 먹방
    lst[y][x] = None

    # 물고기의 이동
    # 1번부터 16번까지 물고기 이동 (없으면 패스)

    # 1번부터 찾기
    for i in range(1, 16+1):
        for j in range(16):
            if lst[j//4][j%4][0] == i:
                my_dir = direction[lst[j//4][j%4][1]]

                # 8방향 검사
                for i in range(8):
                    # 그쪽 방향으로 갈수 있는가??
                    if (0 <= (y + my_dir[0]) < 4) and (0 <= (x + my_dir[1]) < 4):
                        # 자리 교체
                        temp = deepcopy(lst[j//4][j%4])
                        lst[j//4][j%4] = (lst[j//4][j%4])
                        break
                    # 못가면
                    else:
                        # 45도 회전 이후 다시 검사
                        my_dir = direction[lst[j//4][j%4][1]]-1