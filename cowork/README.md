# Cowork 에서 쓰기

Cowork 에는 Claude Code 의 훅이 없다. 대신 세 가지로 같은 효과를 낸다.

1. 계정 스킬로 `skills/noslop-write`, `skills/noslop-review`, `skills/noslop-fix` 를 저장한다. 세 스킬의 description 이 트리거다.
2. 린터는 호스트에서 돈다. Desktop Commander 로 `python3 -m noslop lint <파일>` 을 실행한다. 샌드박스에서 만든 파일은 outputs 경로를 그대로 넘기면 된다.
3. 세션 시작 규칙(N1)은 Cowork 의 사용자 지침(preferences)에 `python3 -m noslop rules --register chat` 출력을 붙여 넣는다. 40줄이 안 된다.

Desktop Commander 실행 예:

```
start_process: cd ~/.noslop/noslop && python3 -m noslop lint "/path/to/산출물.md" --register prose
```

## 클라우드 세션

클라우드에서 도는 Cowork 세션은 샌드박스와 호스트가 다른 머신이다. 샌드박스의 outputs 경로를 호스트 린터에 넘기면 파일을 찾지 못한다. 이때는 샌드박스에 린터를 깐다. 세 스킬의 실행 위치 절에 같은 명령이 들어 있다.

```
[ -d ~/.noslop-src ] || git clone --depth 1 https://github.com/hsol/noslop ~/.noslop-src
python3 -m pip install -e ~/.noslop-src 2>/dev/null || python3 -m pip install --break-system-packages -e ~/.noslop-src
```

개인 프로필은 기본값으로 `~/.noslop/profile.yaml` 을 읽는다. 클라우드 샌드박스에는 이 파일이 없으므로 정본 규칙만 적용된다. 개인 규칙까지 걸려면 프로필을 샌드박스의 같은 경로에 만들거나 `--profile` 로 넘긴다.

Google Drive 동기 폴더의 파일은 클라우드 전용 상태면 샌드박스에서 안 보인다. 호스트에서 돌리면 문제없다.
