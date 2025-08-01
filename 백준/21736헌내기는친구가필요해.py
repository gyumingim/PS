from collections import deque

N, M = map(int, input().split())

graph = []
point = ()
answer = 0


visited = [[0]*M for _ in range(N)]

for i in range(N):
    graph.append([])
    a = input()
    for index, k in enumerate(a):
        graph[i].append(k)
        if k == "I":
            point = (i, index)


queue = deque()
queue.append(point)

visited[point[0]][point[1]] = 1

while queue:
    y, x = queue.popleft()

    for yy, xx in [[-1, 0], [1, 0], [0, 1], [0, -1]]:
        # 장애물 감지, y, x 위치가 범위를 벗어나지 않는지
        # visited가 아닌지
        if 0 <= y+yy < N and 0 <= x+xx < M and \
            graph[y+yy][x+xx] != "X" and \
            visited[y+yy][x+xx] == 0:

            # 아니라면 추가
            queue.append((y+yy, x+xx))

            # 그리고 visited 추가
            visited[y+yy][x+xx] = 1

            # 만약 학생이라면
            if graph[y+yy][x+xx] == "P":
                answer += 1

if answer == 0:
    print('TT')
else:
    print(answer)