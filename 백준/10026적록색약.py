from collections import deque

N = int(input())

graph = []

visited = [[0]*N for _ in range(N)]
visited_2 = [[0]*N for _ in range(N)]
answer_1 = 0
answer_2 = 0

for i in range(N):
    graph.append([])
    a = input()
    for k in a:
        graph[i].append(k)


queue = deque()

for i in range(N):
    for j in range(N):
        if visited[i][j] == 0:
            answer_1 += 1
            queue.append((i, j, graph[i][j]))
            visited[i][j] = 1
            while queue:
                y, x, my_color = queue.popleft()

                for yy, xx in [[-1, 0], [1, 0], [0, 1], [0, -1]]:
                    # 장애물 감지, y, x 위치가 범위를 벗어나지 않는지
                    # visited가 아닌지
                    if 0 <= y+yy < N and 0 <= x+xx < N and \
                        graph[y+yy][x+xx] == my_color and \
                        visited[y+yy][x+xx] == 0:

                        # 아니라면 추가
                        queue.append((y+yy, x+xx, my_color))

                        # 그리고 visited 추가
                        visited[y+yy][x+xx] = 1

for i in range(N):
    for j in range(N):
        if graph[i][j] == 'G':
            graph[i][j] = 'R'

queue = deque()

for i in range(N):
    for j in range(N):
        if visited_2[i][j] == 0:
            answer_2 += 1
            queue.append((i, j, graph[i][j]))
            visited_2[i][j] = 1
            while queue:
                y, x, my_color = queue.popleft()

                for yy, xx in [[-1, 0], [1, 0], [0, 1], [0, -1]]:
                    # 장애물 감지, y, x 위치가 범위를 벗어나지 않는지
                    # visited가 아닌지
                    if 0 <= y+yy < N and 0 <= x+xx < N and \
                        graph[y+yy][x+xx] == my_color and \
                        visited_2[y+yy][x+xx] == 0:

                        # 아니라면 추가 
                        queue.append((y+yy, x+xx, my_color))

                        # 그리고 visited_2 추가
                        visited_2[y+yy][x+xx] = 1

print(answer_1, answer_2)