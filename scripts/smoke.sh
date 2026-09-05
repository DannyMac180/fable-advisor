#!/bin/sh
# arch-advisor — smoke test the codex side of each lane.
#
# Proves the exact invocation a lane agent will make actually reaches the model:
# lane resolves, effort validates, codex authenticates, the model answers.
# Deliberately tiny -- a few thousand tokens per lane, not a real task.
#
#   smoke.sh                 test the active lanes of every profile (a few tokens)
#   smoke.sh --dry-run       print the commands without calling codex (free)
#   smoke.sh --profile codex test only the lanes active in one profile
#   smoke.sh <lane>          test one lane only, active or not
#   smoke.sh --effort max    test at a specific rung instead of the lowest
#   smoke.sh --all-lanes     include lanes that are active in no profile

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LANE_SH="$script_dir/lane.sh"
[ -x "$LANE_SH" ] || { echo "smoke: cannot find lane.sh next to this script" >&2; exit 3; }

DRY=0; EFFORT=""; ONLY=""; PROFILE=""; ALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)   DRY=1 ;;
    --effort)    EFFORT="${2:-}"; shift ;;
    --profile)   PROFILE="${2:-}"; shift ;;
    --all-lanes) ALL=1 ;;
    -h|--help)   sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)          echo "smoke: unknown flag $1" >&2; exit 2 ;;
    *)           ONLY="$1" ;;
  esac
  shift
done

command -v codex >/dev/null 2>&1 || { echo "smoke: codex not on PATH" >&2; exit 3; }
[ "$DRY" = "1" ] || codex login status >/dev/null 2>&1 || { echo "smoke: codex not authenticated (run: codex login)" >&2; exit 3; }

CONFIG=$("$LANE_SH" config-path)

# Default to the union of every profile's active lanes: testing a lane no profile
# routes to spends tokens proving nothing. --all-lanes and an explicit lane opt out.
if [ -n "$ONLY" ]; then
  LANES="$ONLY"
elif [ "$ALL" = "1" ]; then
  LANES=$(jq -r '.lanes | keys_unsorted[]' "$CONFIG")
elif [ -n "$PROFILE" ]; then
  "$LANE_SH" profile "$PROFILE" >/dev/null   # fails loudly on an unknown profile
  LANES=$(jq -r --arg p "$PROFILE" '.profiles[$p].lanes[]' "$CONFIG")
else
  LANES=$(jq -r '[.profiles[].lanes[]] | unique[]' "$CONFIG")
fi
[ -n "$LANES" ] || { echo "smoke: no lanes selected" >&2; exit 2; }

rc=0
for lane in $LANES; do
  eval "$("$LANE_SH" resolve "$lane")"

  # Lowest declared rung unless one was asked for: cheapest thing that still proves the path.
  e="$EFFORT"
  [ -z "$e" ] && [ "$LANE_EFFORTS_DECLARED" = "1" ] && e=$(echo "$LANE_EFFORTS" | cut -d' ' -f1)
  if [ -n "$e" ] && ! "$LANE_SH" validate "$lane" "$e" 2>/dev/null; then
    printf '%-9s SKIP    effort %s not declared for %s\n' "$lane" "$e" "$LANE_MODEL"; rc=1; continue
  fi

  if [ "$DRY" = "1" ]; then
    printf '%-9s DRY     codex exec --model %s%s --sandbox read-only\n' \
      "$lane" "$LANE_MODEL" "$([ -n "$e" ] && echo " -c model_reasoning_effort=$e")"
    continue
  fi

  out=$(codex exec --skip-git-repo-check --sandbox read-only \
          --model "$LANE_MODEL" \
          ${e:+-c model_reasoning_effort=$e} \
          "Reply with exactly: OK" < /dev/null 2>&1) || true

  if echo "$out" | grep -q '"message":'; then
    printf '%-9s FAIL    %s\n' "$lane" "$(echo "$out" | grep -o '"message": "[^"]*"' | head -1 | cut -c12-)"
    rc=1
  elif echo "$out" | grep -qx 'OK'; then
    printf '%-9s ok      %s effort=%s tokens=%s\n' "$lane" "$LANE_MODEL" "${e:-<codex default>}" \
      "$(echo "$out" | grep -A1 'tokens used' | tail -1 | tr -d ' ')"
  else
    printf '%-9s FAIL    no clean reply from %s\n' "$lane" "$LANE_MODEL"; rc=1
  fi
done
exit $rc
