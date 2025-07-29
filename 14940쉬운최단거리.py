N, M = map(int, input().split())

lst = []

# 입력 받기
for _ in range(N):
    lst.append(list(map(int, input().split())))

point = []

# 2 위치 찾기
for i in range(N):
    for j in range(M):
        if lst[i][j] == 2:
            point = [i, j]
            break
    
    # 찾았으면 나가기
    if point != []:
        break

# bfs로 숫자채우기
# 만약 이미 숫자가 있다면 그쪽으로는 안보내기
# 무한반복
queue = []
queue.append(point + [-9999])

lst[point[0]][point[1]] = 0

while queue:
    yy, xx, my_depth = queue.pop(0)

    for y_plus, x_plus in [[1, 0], [0, 1], [-1, 0], [0, -1]]:
        if 0 <= yy+y_plus < N and 0 <= xx+x_plus < M:
            if lst[yy+y_plus][xx+x_plus] == 1 and lst[yy+y_plus][xx+x_plus] > my_depth and lst[yy+y_plus][xx+x_plus] != 0:
                lst[yy+y_plus][xx+x_plus] = my_depth
                queue.append([yy+y_plus, xx+x_plus, my_depth+1])

for i in lst:
    for j in i:
        if j == 0:
            print(0, end=" ")
            continue
        if j == 1:
            print(-1, end=" ")
            continue
        print(j+10000, end=" ")
    print()