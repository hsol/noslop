#!/usr/bin/env bash
# Claude Code PostToolUse 훅 (Write|Edit|MultiEdit). 저장된 파일이 md/txt/docx/pptx면 noslop lint를 돌린다.
# exit 2 이면 stderr 내용이 Claude에게 차단 사유로 전달되고, Claude는 같은 턴에서 고쳐 다시 저장한다.
NOSLOP_HOME="${NOSLOP_HOME:-$HOME/.noslop}"
export NOSLOP_PROFILE="${NOSLOP_PROFILE:-$NOSLOP_HOME/profile.yaml}"
export PYTHONPATH="$NOSLOP_HOME/noslop:$PYTHONPATH"
exec python3 -m noslop hook
