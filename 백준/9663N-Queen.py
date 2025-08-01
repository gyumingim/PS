# """Baekjoon 9663 N-Queen – readable backtracking solution.

# 가독성을 위해 열ㆍ대각선 점유 여부를 **리스트**로 관리합니다.
# 시간 복잡도는 비트마스크 버전과 동일한 O(N!) 이지만, 파이썬에서도 N ≤ 15 제한을
# 충분히 만족합니다.
# """

# import sys

# # 입력
# N = int(sys.stdin.readline())

# # 충돌 여부를 기록하는 배열들
# cols = [False] * N               # 각 열에 퀸이 있는지
# diag1 = [False] * (2 * N - 1)    # ↙ 대각선(row + col)
# diag2 = [False] * (2 * N - 1)    # ↘ 대각선(row - col + N - 1)


# def dfs(row: int) -> int:
#     """row번째 행에 퀸을 배치하고, 가능한 해의 개수를 반환합니다."""-=]\    if row == N:
#         return 1  # 모든 행에 배치 완료

#     count = 0
#     for col in range(N):
#         d1 = row + col          # ↙ 대각선 인덱스
#         d2 = row - col + N - 1  # ↘ 대각선 인덱스

#         # 이미 점유된 곳이면 건너뛰기
#         if cols[col] or diag1[d1] or diag2[d2]:
#             continue

#         # 퀸 배치
#         cols[col] = diag1[d1] = diag2[d2] = True
#         count += dfs(row + 1)ag1[d1] = diag2[d2] = False

#     return count


# print(dfs(0))\\\\\\\\\\\\\\\\\\\\\\1`2`



