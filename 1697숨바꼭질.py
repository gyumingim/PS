from collections import deque

N, M = map(int, input().split())

visited = [0] * 1000000

queue = deque()
queue.append((N, 0))

while queue:
    a, depth = queue.popleft()
    if (a == M):
        print(depth)
        exit()
    
    if 0<=a<100001 and not visited[a*2]:
        queue.append((a*2, depth+1))
        visited[a*2] = 1
    if 0<=a<100001 and not visited[a-1]:
        queue.append((a-1, depth+1))
        visited[a-1] = 1
    if 0<=a<100001 and not visited[a+1]:
        queue.append((a+1, depth+1))
        visited[a+1] = 1

