# noslop

한국어 AI 슬롭이 산출물에 들어오지 못하게 막는 파이프라인이다. 사후 윤문은 마지막 수단으로만 쓴다. 슬롭이 들어오는 세 지점을 각각 다른 노드가 막는다.

## 고치기 전과 후

같은 내용을 두 번 썼다. 앞의 것은 모델이 기본 문체로 쓴 글이고, 뒤의 것은 noslop 을 거쳐 다시 쓴 글이다.

**전**

```text
결론부터 말하면, 회의록 자동화는 단순한 편의 기능이 아니라 팀의 일하는 방식을 바꾸는 도구입니다.
이 글에서는 저희 팀이 회의록 자동화를 도입한 과정을 살펴보겠습니다.

도입 효과는 세 가지로 정리할 수 있습니다.
첫째, 회의 내용이 빠짐없이 기록되어집니다.
둘째, 담당자가 명확해지고, 후속 작업이 빨라집니다.
셋째, 누구나 지난 논의를 쉽게 찾을 수 있도록, 검색이 가능해집니다.

결론적으로, 회의록 자동화는 매우 효과적인 선택이었습니다.
데이터가 말해주듯이, 팀의 생산성은 크게 향상되었습니다.
시사하는 바가 큽니다.
도움이 되셨길 바랍니다.
```

```
$ noslop lint before.md
BLOCK 4 / REVIEW 3  (문장 10, 쉼표문장 60%)
  [BLOCK B02] 부정-대조 골격   L1  ...단순한 편의 기능이 아니라 팀의 일하는 방식을 바꾸는 도구입니다.
  [BLOCK B06] 헛기침 도입      L1  이 글에서는 ... 살펴보겠습니다.
  [BLOCK B03] 열거 라벨        L3  첫째, ... 둘째, ... 셋째, ...
  [BLOCK B07] 챗봇 잔재        L5  도움이 되셨길 바랍니다.
  [review R12] 무생물 주어 + 사람 동사  L5  데이터가 말해주듯이
  [review R02] 쉼표 포함 문장 비율      60%
  [review R03] 종결어미 연속            10연속
총 BLOCK 4건. 제출 불가

$ noslop score before.md
score=66 threshold=40 QUARANTINE
```

**후**

```text
지난달부터 회의가 끝나면 녹음 파일을 올리고 회의록 초안을 자동으로 받습니다.
사람이 쓰던 때는 회의록이 보통 다음 날 오후에 올라왔고, 바쁜 주에는 아예 안 올라온 적도 있습니다.

가장 크게 달라진 건 결정 사항 옆에 담당자 이름이 붙어 나온다는 점입니다.
예전에는 "그건 누가 하기로 했죠?" 를 묻느라 다음 회의 첫 10분을 썼는데 요즘은 그 질문이 거의 나오지 않습니다.
석 달 전 논의도 키워드로 찾으면 바로 나옵니다.

아쉬운 점도 있습니다.
여러 사람이 동시에 말하면 발언자를 자주 헷갈려서 진행자가 초안을 올리기 전에 5분쯤 손을 봅니다.
그 5분을 빼도 회의록에 쓰던 시간은 절반 아래로 줄었습니다.
```

```
$ noslop lint after.md
BLOCK 0 / REVIEW 1  (문장 8, 쉼표문장 12%)
  [review R03] 종결어미 연속  8연속
총 BLOCK 0건. 제출 가능 (REVIEW는 하나씩 판정)

$ noslop score after.md
score=6 threshold=40 ok
```

앞의 글은 문장마다 틀린 곳이 없는데도 읽고 나면 남는 사실이 없다. 결론을 예고하고 셋으로 나눈 뒤 다시 결론으로 묶는 틀만 있고, 그 안에 들어갈 내용이 빠져 있다. 뒤의 글은 언제부터 무엇이 바뀌었는지, 무엇이 아직 불편한지를 적었고, 린터가 남긴 REVIEW 1건은 합쇼체로 쓴 글이라 판정하고 그대로 두었다.

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

`noslop` 은 install.sh 가 깔아 주는 콘솔 스크립트다. PATH 에 없으면 `python3 -m noslop` 으로 똑같이 쓴다.

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

## 골든 코퍼스 실측 (2026-09-16)

저자가 2010년대에 직접 쓴 블로그 1,014편(16,810문장)으로 잰 BLOCK 규칙의 파일 단위 오탐률이다.

| 규칙 | 파일 비율 | 처리 |
|---|---|---|
| B01 글리프 | 1.7% | BLOCK 유지. 고치는 비용이 0이고 뜻을 건드리지 않는다. 가운뎃점, 참고표, 낫표는 핵심에서 빼고 개인 프로필로 넘겼다 |
| B04 개수 예고 | 1.0% | "두 개 이상 있을 때" 같은 수량 표현을 제외하고 선언 뒤 두 문장 안에서만 센다 |
| B02 부정-대조 | 3.0% -> 0.4% | 수사적 대조만 BLOCK, 일반형은 R15(REVIEW, 문서당 2회 초과)로 |
| B09 헤딩 반복 | 1.9% -> 0.2% | H1 은 본문 첫 줄이 제목을 되풀이하는 포맷이 흔해 제외 |

개인 프로필의 P 규칙은 저자가 뒤늦게 세운 금지 규칙이라 옛 글에서 1~3% 나오는 것이 정상이다.
