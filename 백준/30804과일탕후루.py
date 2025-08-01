'''
bfs로 
'''
from collections import deque


N = int(input())

lst = list(map(int, input().split()))


queue = deque()
queue.append((0, len(lst)))

while queue:
    front, rear = queue.popleft()
    if len(set(lst[front:rear])) <= 2:
        print(rear-front)
        exit()
    queue.append((front+1, rear))
    queue.append((front, rear-1))