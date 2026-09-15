# Cowork 에서 쓰기

Cowork 에는 Claude Code 의 훅이 없다. 대신 세 가지로 같은 효과를 낸다.

1. 계정 스킬로 `skills/noslop-write`, `skills/noslop-review`, `skills/noslop-fix` 를 저장한다. 세 스킬의 description 이 트리거다.
2. 린터는 호스트에서 돈다. Desktop Commander 로 `python3 -m noslop lint <파일>` 을 실행한다. 샌드박스에서 만든 파일은 outputs 경로를 그대로 넘기면 된다.
3. 세션 시작 규칙(N1)은 Cowork 의 사용자 지침(preferences)에 `python3 -m noslop rules --register chat` 출력을 붙여 넣는다. 40줄이 안 된다.

Desktop Commander 실행 예:

```
start_process: cd ~/.noslop/noslop && python3 -m noslop lint "/path/to/산출물.md" --register prose
```

Google Drive 동기 폴더의 파일은 클라우드 전용 상태면 샌드박스에서 안 보인다. 호스트에서 돌리면 문제없다.
