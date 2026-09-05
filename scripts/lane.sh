#!/bin/sh
# arch-advisor — profile and lane resolver.
#
# A profile says who architects and who reviews; a lane says who implements.
# Both live in lanes.json. This script resolves them and validates a requested
# reasoning effort against the lane that will run it.
#
# The codex CLI does NOT validate `model_reasoning_effort` client-side: it prints
# whatever you give it and lets the API reject it later. This script is where the
# "refuse rather than round" promise is actually kept.
#
#   lane.sh list                          profiles and lanes in effect
#   lane.sh profiles                      names of configured profiles
#   lane.sh profile <profile>             shell-eval-able PROFILE_* assignments
#   lane.sh resolve <lane>                shell-eval-able LANE_* assignments
#   lane.sh validate <lane> <effort>      exit 0 if the rung is declared for that lane
#   lane.sh lane-active <profile> <lane>  exit 0 if the lane is active in that profile
#   lane.sh config-path                   path of the lanes.json in effect

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

profile_exists() { jq -e --arg p "$1" '.profiles | has($p)' "$CONFIG" >/dev/null 2>&1; }
profile_names()  { jq -r '.profiles | keys_unsorted | join(", ")' "$CONFIG"; }

require_lane() {
  lane_exists "$1" || die "unknown lane '$1' in $CONFIG (configured: $(lane_names))" 2
}

require_profile() {
  profile_exists "$1" || die "unknown profile '$1' in $CONFIG (configured: $(profile_names))" 2
}

cmd=${1:-}
case "$cmd" in
  config-path)
    printf '%s\n' "$CONFIG"
    ;;

  list)
    printf 'lanes.json: %s\n\n' "$CONFIG"
    printf 'PROFILES\n\n'
    jq -r '.profiles | to_entries[] |
      "  \(.key)  [host: \(.value.host)]\n    architect: \(.value.architect)\(if .value.architect_fallback == null then "" else " (fallback: " + .value.architect_fallback + ")" end)\n    advisor:   \(.value.advisor_model) via \(.value.advisor_kind)\n    lanes:     \(.value.lanes | join(", "))\n    \(.value.describe)\n"' "$CONFIG"
    printf 'LANES\n\n'
    jq -r '. as $root | .lanes | to_entries[] |
      . as $lane |
      ($root.profiles | to_entries | map(select(.value.lanes | index($lane.key))) | map(.key)) as $active |
      "  \(.key)\(if ($active | length) == 0 then "  [INACTIVE — in no profile]" else "  [active in: " + ($active | join(", ")) + "]" end)\n    agent:   \(.value.agent)\n    model:   \(.value.model)\n    efforts: \(if .value.efforts == null then "(not declared — the flag is omitted and codex uses your ~/.codex/config.toml default)" else (.value.efforts | join(", ")) end)\n    timeout: \(.value.timeout_seconds)s\n"' "$CONFIG"
    ;;

  profiles)
    jq -r '.profiles | keys_unsorted[]' "$CONFIG"
    ;;

  profile)
    profile=${2:-}; [ -n "$profile" ] || die "usage: lane.sh profile <profile>" 2
    require_profile "$profile"
    # Values are single-quoted: PROFILE_LANES is a space-separated list, and an
    # unquoted eval of it would run the second lane name as a command.
    jq -r --arg p "$profile" '
      def q: "\u0027" + (tostring | gsub("\u0027"; "\u0027\\\\\u0027\u0027")) + "\u0027";
      .profiles[$p] |
      "PROFILE_NAME=" + ($p | q),
      "PROFILE_HOST=" + (.host | q),
      "PROFILE_ARCHITECT=" + (.architect | q),
      "PROFILE_ARCHITECT_FALLBACK=" + ((if .architect_fallback == null then "" else .architect_fallback end) | q),
      "PROFILE_ADVISOR_KIND=" + (.advisor_kind | q),
      "PROFILE_ADVISOR_MODEL=" + (.advisor_model | q),
      "PROFILE_ADVISOR_FALLBACK=" + ((if .advisor_fallback == null then "" else .advisor_fallback end) | q),
      "PROFILE_LANES=" + ((.lanes | join(" ")) | q)' "$CONFIG"
    ;;

  resolve)
    lane=${2:-}; [ -n "$lane" ] || die "usage: lane.sh resolve <lane>" 2
    require_lane "$lane"
    # Same reason: LANE_EFFORTS is a space-separated list.
    jq -r --arg l "$lane" '
      def q: "\u0027" + (tostring | gsub("\u0027"; "\u0027\\\\\u0027\u0027")) + "\u0027";
      .lanes[$l] |
      "LANE_NAME=" + ($l | q),
      "LANE_MODEL=" + (.model | q),
      "LANE_TIMEOUT=" + (.timeout_seconds | q),
      "LANE_EFFORTS=" + ((if .efforts == null then "" else (.efforts | join(" ")) end) | q),
      "LANE_EFFORTS_DECLARED=" + ((if .efforts == null then 0 else 1 end) | q)' "$CONFIG"
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

  lane-active)
    profile=${2:-}; lane=${3:-}
    [ -n "$profile" ] && [ -n "$lane" ] || die "usage: lane.sh lane-active <profile> <lane>" 2
    require_profile "$profile"
    require_lane "$lane"
    if jq -e --arg p "$profile" --arg l "$lane" '.profiles[$p].lanes | index($l)' "$CONFIG" >/dev/null 2>&1; then
      exit 0
    fi
    active=$(jq -r --arg p "$profile" '.profiles[$p].lanes | join(", ")' "$CONFIG")
    die "lane '$lane' is not active in profile '$profile' (active: $active). Add it to that profile's lanes array to enable it." 5
    ;;

  ""|-h|--help|help)
    sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
    ;;

  *)
    die "unknown command '$cmd' (try: list, profiles, profile, resolve, validate, lane-active, config-path)" 2
    ;;
esac
