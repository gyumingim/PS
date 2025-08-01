from sys import stdin
input = stdin.readline

num = int(input())

column1 = list(range(num, 0, -1))
column2 = []
column3 = []

def DrawDisk():
    print(column1)
    print(column2)
    print(column3)
    print()

def MoveDisk(size, depart, arrival, other):
    if (size == 1):
        arrival.append(depart.pop())
        DrawDisk()
    else:
        MoveDisk(size-1, depart, other, arrival)
        arrival.append(depart.pop())
        DrawDisk()
        MoveDisk(size-1, other, arrival, depart)

DrawDisk()
MoveDisk(num, column1, column3, column2)