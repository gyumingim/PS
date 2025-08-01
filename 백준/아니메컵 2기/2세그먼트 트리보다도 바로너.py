n = int(input())
algorithms = [tuple(input().split()) for _ in range(n)]
algorithms = [(name, int(diff)) for name, diff in algorithms]

m = int(input())
members = {name: int(tier) for name, tier in (input().split() for _ in range(m))}

q = int(input())
current = None 
breakpoint()
for _ in range(q):
    line = input().rstrip('\n')
    if line.endswith('- chan!'):
        current = line.split(' - ')[0]
        print('hai!')
    else:  # "nani ga suki?"
        tier = members[current]
        best_two = sorted(algorithms, key=lambda x: (abs(x[1] - tier), x[0]))[:2]
        print(f"{best_two[1][0]} yori mo {best_two[0][0]}")
