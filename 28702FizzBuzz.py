A = input()
B = input()
C = input()

answer = 0

try:
    A = int(A)
    answer = A+3
except:
    pass

try:
    B = int(B)
    answer = B+2
except:
    pass

try:
    C = int(C)
    answer = C+1
except:
    pass

if answer%3==0 and answer%5==0:
    print("FizzBuzz")
    exit()
if answer%3==0:
    print("Fizz")
    exit()
if answer%5==0:
    print("Buzz")
    exit()
print(answer)