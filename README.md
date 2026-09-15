# noslop

한국어 AI 슬롭이 산출물에 들어오지 못하게 막는 파이프라인이다. 사후 윤문은 마지막 수단으로만 쓴다. 슬롭이 들어오는 세 지점을 각각 다른 노드가 막는다.

| 지점 | 노드 | 형태 |
|---|---|---|
| 생성할 때 모델의 기본 문체가 나온다 | N1 예방: 세션 시작마다 40줄 규칙 주입, 출력 스타일 | `hooks/session-start.sh`, `claude/output-styles/noslop.md` |
| 참조 자료의 AI 문장이 새 글로 옮겨 붙는다 | N2 격리: 자료를 읽기 전에 점수를 매기고, 높으면 사실만 추출 | `noslop score`, `skills/noslop-write` 2단계 |
| 산출물에 남는다 | N4 게이트: LLM 없이 도는 린터가 저장 시점에 차단 | `noslop lint`, `hooks/post-tool-use.sh`, pre-commit |
| 고치다가 더 망가진다 | N5 판단: 탐지, 수술, 독립 감사, 재린트 루프 | `skills/noslop-review` |
| 남의 슬롭이 내 글에 다시 들어온다 | N6 습관: 발견하면 backlog, 내 파일은 별도 커밋, 주 1회 sweep | `skills/noslop-fix`, `noslop sweep` |
| 규칙이 사람 글을 잡는다 | N7 평가: 본인 글 코퍼스로 오탐률 측정 | `eval/run_eval.py` |

규칙의 정본은 `rules/rules.yaml` 하나다. 어휘 블랙리스트를 쌓지 않고 구조와 통계로 판정한다. 근거는 KatFishNet(ACL 2025), LREAD(2026), XDAC(ACL 2025), 국립국어원 번역투 연구에서 가져왔다.

## 설치

```
git clone https://github.com/<owner>/noslop ~/.noslop-src && ~/.noslop-src/install.sh
```

Claude Code 는 `claude/settings.snippet.json` 의 훅을 settings.json 에 합치고 `/output-style noslop` 을 켠다. Cowork 는 `cowork/README.md` 를 본다.

## 명령

```
noslop lint 파일.md [--register prose|docs|social|chat|formal] [--block-only] [--json]
noslop score 파일.md          # 참조 격리용 0~100. 임계(40) 이상이면 exit 3
noslop sweep 디렉터리 --top 10  # 저장소 전수 점검
noslop rules --register chat   # 세션 주입용 요약
noslop hook                    # PostToolUse 훅 진입점
```

md, txt, docx, pptx 를 받는다. pptx 는 발표자 노트까지 본다. `kiwipiepy` 가 있으면 품사 다양성과 명사 나열 규칙이 켜진다.

## 판정 원칙

- BLOCK 은 구조로 확정되는 것만. 하나라도 남으면 산출물이 나가지 않는다.
- REVIEW 는 통계 신호. 남길 이유를 하나씩 정한다.
- 매체(register)에 따라 규칙을 끈다. 보고서에서 첫째둘째는 정상이다.
- 사실, 수치, 고유명사, 인용, 코드는 어떤 규칙도 건드리지 않는다.
- "AI가 썼다"고 판정하지 않는다. 신호가 있다고만 말한다.

## 개인 규칙

`profiles/example-personal.yaml` 을 `~/.noslop/profile.yaml` 로 복사해 고친다. 정본 위에 얹히고, 정본은 공유판으로 유지한다.

## 규칙을 추가할 때

1. `eval/golden/` 에 본인이 쓴 글을 넣는다.
2. 규칙을 `rules/rules.yaml` 에 REVIEW 로 넣는다.
3. `python3 eval/run_eval.py` 로 오탐률을 본다. 1% 이하일 때만 BLOCK 으로 올린다.
4. `python3 -m pytest tests` 를 돈다.

## 라이선스

MIT
