#!/bin/sh
# arch-advisor — lane resolver.
#
# Resolves a lane name to the codex model, effort rungs and timeout declared in
# lanes.json, and validates a requested reasoning effort against that lane.
#
# The codex CLI does NOT validate `model_reasoning_effort` client-side: it prints
# whatever you give it and lets the API reject it later. This script is where the
# "refuse rather than round" promise is actually kept.
#
#   lane.sh list                     human-readable table of configured lanes
#   lane.sh resolve <lane>           shell-eval-able LANE_* assignments
#   lane.sh validate <lane> <effort> exit 0 if the rung is declared for that lane
#   lane.sh config-path              path of the lanes.json in effect

set -eu

die() { echo "arch-advisor: $1" >&2; exit "${2:-1}"; }

command -v jq >/dev/null 2>&1 || die "jq is required but not on PATH (brew install jq)" 3

find_config() {
  [ -n "${ARCH_ADVISOR_CONFIG:-}" ] && { [ -f "$ARCH_ADVISOR_CONFIG" ] || die "ARCH_ADVISOR_CONFIG points at a missing file: $ARCH_ADVISOR_CONFIG" 3; printf '%s\n' "$ARCH_ADVISOR_CONFIG"; return; }
  script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  for candidate in \
    "$PWD/.arch-advisor/lanes.json" \
    "$HOME/.claude/arch-advisor/lanes.json" \
    "$script_dir/../config/lanes.json"
  do
    [ -f "$candidate" ] && { printf '%s\n' "$candidate"; return; }
  done
  die "no lanes.json found (looked in \$ARCH_ADVISOR_CONFIG, ./.arch-advisor/, ~/.claude/arch-advisor/, and the plugin's config/)" 3
}

CONFIG=$(find_config)
jq -e . "$CONFIG" >/dev/null 2>&1 || die "lanes.json is not valid JSON: $CONFIG" 3

lane_exists() { jq -e --arg l "$1" '.lanes | has($l)' "$CONFIG" >/dev/null 2>&1; }
lane_names()  { jq -r '.lanes | keys_unsorted | join(", ")' "$CONFIG"; }

require_lane() {
  lane_exists "$1" || die "unknown lane '$1' in $CONFIG (configured: $(lane_names))" 2
}

cmd=${1:-}
case "$cmd" in
  config-path)
    printf '%s\n' "$CONFIG"
    ;;

  list)
    printf 'lanes.json: %s\n\n' "$CONFIG"
    jq -r '.lanes | to_entries[] |
      "  \(.key)\n    agent:   \(.value.agent)\n    model:   \(.value.model)\n    efforts: \(if .value.efforts == null then "(not declared — the flag is omitted and codex uses your ~/.codex/config.toml default)" else (.value.efforts | join(", ")) end)\n    timeout: \(.value.timeout_seconds)s\n"' "$CONFIG"
    ;;

  resolve)
    lane=${2:-}; [ -n "$lane" ] || die "usage: lane.sh resolve <lane>" 2
    require_lane "$lane"
    jq -r --arg l "$lane" '.lanes[$l] |
      "LANE_NAME=\($l)",
      "LANE_MODEL=\(.model)",
      "LANE_TIMEOUT=\(.timeout_seconds)",
      "LANE_EFFORTS=\(if .efforts == null then "" else (.efforts | join(" ")) end)",
      "LANE_EFFORTS_DECLARED=\(if .efforts == null then 0 else 1 end)"' "$CONFIG"
    ;;

  validate)
    lane=${2:-}; effort=${3:-}
    [ -n "$lane" ] && [ -n "$effort" ] || die "usage: lane.sh validate <lane> <effort>" 2
    require_lane "$lane"
    model=$(jq -r --arg l "$lane" '.lanes[$l].model' "$CONFIG")
    if jq -e --arg l "$lane" '.lanes[$l].efforts == null' "$CONFIG" >/dev/null 2>&1; then
      die "effort rungs for '$model' (lane '$lane') are not declared in $CONFIG. Omit the effort flag so codex uses your own default, or declare the rungs once you have confirmed them." 4
    fi
    if jq -e --arg l "$lane" --arg e "$effort" '.lanes[$l].efforts | index($e)' "$CONFIG" >/dev/null 2>&1; then
      exit 0
    fi
    valid=$(jq -r --arg l "$lane" '.lanes[$l].efforts | join(", ")' "$CONFIG")
    die "effort '$effort' is not supported by $model (lane '$lane'). Declared rungs: $valid. Refusing rather than rounding." 4
    ;;

  ""|-h|--help|help)
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
    ;;

  *)
    die "unknown command '$cmd' (try: list, resolve, validate, config-path)" 2
    ;;
esac
