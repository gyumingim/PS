'''
다 때려박으면 안되나??

해봐야지

큰 자리수에 큰 수를 대입하는건 안되는 방법임, 모든 경우의 수?

글자수 만큼 모든 경우의 수를 대입하는

ㄴㄴ

알파벳마다 자릿수를 전부 더해서
높은만큼 9,8,7 을 할당하면 된다

수치
'''
N = int(input())
word_list = [input().strip() for _ in range(N)]
alphabet = {}


for word in word_list:
    digit = len(word) - 1
    for w in word:
        if w in alphabet:
            alphabet[w] += 10**digit
        else:
            alphabet[w] = 10**digit
        digit -= 1


words_sort = sorted(alphabet.values(), reverse=True) 
result = 0
num = 9
for k in words_sort:
    result += k * num 
    num -= 1
print(result)