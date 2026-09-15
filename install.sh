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
python3 -c "import yaml" 2>/dev/null || pip3 install --user pyyaml
echo "설치 끝. 다음을 한다:"
echo "1) ~/.claude/settings.json 의 hooks 에 claude/settings.snippet.json 내용을 합친다"
echo "2) Claude Code 에서 /output-style noslop"
echo "3) 개인 규칙은 ~/.noslop/profile.yaml 에서 고친다"
echo "4) 확인: echo '{\"tool_input\":{\"file_path\":\"$SRC/tests/fixtures/slop.md\"}}' | bash ~/.noslop/hooks/post-tool-use.sh"
