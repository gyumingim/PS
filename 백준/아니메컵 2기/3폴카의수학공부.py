import sys

def is_order_invariant(expr: str) -> bool:
    """주어진 수식이 어떤 괄호 배치에서도 결과가 동일하면 True 반환."""
    # 첫 '-' 위치 찾기 (없으면 항상 YES)
    first_minus = expr.find('-')
    if first_minus == -1:
        return True

    # 첫 '-'가 마지막 연산자라면 괄호 배치가 한 가지뿐 -> 일정함
    if first_minus == len(expr) - 2:
        return True  # (연산자는 맨 끝에서 두 번째 인덱스)

    # 첫 '-' 이후 등장하는 모든 피연산자가 0이면 결과가 변하지 않는다.
    # (x - 0 + 0 - 0 ...) 은 어떤 괄호를 쳐도 값이 같다)
    for i in range(first_minus + 1, len(expr), 2):  # 피연산자는 홀수 인덱스(0-기준 짝수)지만 +2씩 건너뛰며 확인
        if expr[i] != '0':  # 하나라도 0이 아니면 결과가 달라질 수 있다
            return False
    return True


def main() -> None:
    data = sys.stdin.read().splitlines()
    t = int(data[0])
    out_lines = []
    idx = 1
    for _ in range(t):
        n = int(data[idx])  # 사용하지 않음, 길이 검증용
        expr = data[idx + 1].strip()
        idx += 2
        out_lines.append('YES' if is_order_invariant(expr) else 'NO')

    sys.stdout.write('\n'.join(out_lines))


if __name__ == '__main__':
    main()

