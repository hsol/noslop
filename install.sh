#!/usr/bin/env bash
# noslop 설치: ~/.noslop 에 복사하고 Claude Code 훅과 출력 스타일을 연결한다.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$HOME/.noslop"
mkdir -p "$DST" "$HOME/.claude/output-styles" "$HOME/.claude/skills"
rsync -a --delete "$SRC/noslop/" "$DST/noslop/noslop/"
rsync -a "$SRC/rules/" "$DST/noslop/rules/"
rsync -a "$SRC/hooks/" "$DST/hooks/"
cp "$SRC/claude/output-styles/noslop.md" "$HOME/.claude/output-styles/noslop.md"
for s in noslop-write noslop-review noslop-fix; do
  rsync -a "$SRC/skills/$s/" "$HOME/.claude/skills/$s/"
done
[ -f "$DST/profile.yaml" ] || cp "$SRC/profiles/example-personal.yaml" "$DST/profile.yaml"
# 패키지를 editable 로 깐다. 이게 있어야 셸과 에이전트에서 `python3 -m noslop` 이 돈다.
# rules.yaml 을 패키지 상위에서 찾으므로 editable 이어야 한다. pyyaml 은 의존성으로 딸려온다.
python3 -m pip install --user -e "$SRC" 2>/dev/null \
  || python3 -m pip install --user --break-system-packages -e "$SRC"
echo "설치 끝. 다음을 한다:"
echo "1) ~/.claude/settings.json 의 hooks 에 claude/settings.snippet.json 내용을 합친다"
echo "2) Claude Code 에서 /output-style noslop"
echo "3) 개인 규칙은 ~/.noslop/profile.yaml 에서 고친다"
echo "3-1) 짧은 이름 noslop 을 쓰려면 PATH 에 $(python3 -m site --user-base)/bin 을 넣는다. 안 넣어도 python3 -m noslop 은 돈다"
echo "4) 확인: echo '{\"tool_input\":{\"file_path\":\"$SRC/tests/fixtures/slop.md\"}}' | bash ~/.noslop/hooks/post-tool-use.sh"
