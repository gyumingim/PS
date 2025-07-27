N = int(input())

words = input().strip().split()

transformed = (word + "DORO" for word in words)
print(" ".join(transformed))

