#!/usr/bin/env bash
# Claude Code SessionStart 훅. 규칙 요약을 stdout으로 내보내면 세션 컨텍스트에 들어간다.
NOSLOP_HOME="${NOSLOP_HOME:-$HOME/.noslop}"
export NOSLOP_PROFILE="${NOSLOP_PROFILE:-$NOSLOP_HOME/profile.yaml}"
export PYTHONPATH="$NOSLOP_HOME/noslop:$PYTHONPATH"
python3 -m noslop rules --register "${NOSLOP_REGISTER:-chat}"
cat <<'TXT'

## 이 세션의 글쓰기 절차
- 채팅 응답도 산문이다. 위 규칙을 응답에 그대로 적용한다. 생각하는 과정은 자유다.
- 문서를 만들 때는 noslop-write 스킬 순서를 따른다: 매체 확정 -> 참조 격리 -> 무색 초안 -> 보이스 -> lint.
- md/txt/docx/pptx 를 저장하면 훅이 lint를 돌린다. BLOCK이 오면 같은 턴에서 고친다.
- 작업 중 읽은 파일에서 슬롭을 보면 noslop-fix 스킬의 반사 규칙을 따른다.
TXT
