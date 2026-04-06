#!/bin/bash

ENERGY_DIR="/home/vosslab/nsh/energy"

echo "Current tmux sessions:"
tmux list-sessions 2>/dev/null || echo "  (no tmux sessions)"
echo

launch_session() {
  name=$1
  dir=$2
  cmd=$3
  sleep_time=$4

  logfile="/dev/shm/${name}.log"

  if tmux has-session -t "$name" 2>/dev/null; then
    echo "Session '$name' already running."
  else
    echo "Starting '$name'..."
    tmux new-session -d -s "$name" "cd $dir && while true; do $cmd 2>&1 | tee -a \"$logfile\"; sleep $sleep_time; done"
    sleep 2
  fi
}

print_last_tmux_output() {
  name=$1
  logfile="/dev/shm/${name}.log"

  echo -e "\n--- Last visible lines of session: $name ---"

  if [[ -f "$logfile" ]]; then
    # Print last few non-blank lines with color preserved
    grep -v '^\s*$' "$logfile" | tail -n 8
  else
    echo "(no logfile found at $logfile)"
  fi
}

# Launch sessions
# Generates comed.html + dashboard JSON files (replaces separate gen_html session)
launch_session gen_dashboard $ENERGY_DIR "python3 scripts/generate_dashboard_data.py" 150
launch_session wemo $ENERGY_DIR "python3 apps/wemoPlug-comed-multi.py" 300
launch_session awtrix3 $ENERGY_DIR/awtrix3/ "python3 send_price.py" 90
#launch_session log_energy $ENERGY_DIR "python3 logEnergy.py" 300
# Only launch 'summer_ac' during May through September
current_month=$(date +%m)
if (( 5 <= 10#$current_month && 10#$current_month <= 9 )); then
  launch_session summer_ac $ENERGY_DIR "python3 apps/thermostat-comed.py" 300
fi

echo
echo "Updated tmux sessions:"
tmux list-sessions 2>/dev/null || echo "  (no tmux sessions)"

# Show last few lines of session output
print_last_tmux_output gen_dashboard
print_last_tmux_output wemo
print_last_tmux_output awtrix3
#print_last_tmux_output log_energy
if (( 6 <= 10#$current_month && 10#$current_month <= 8 )); then
  print_last_tmux_output summer_ac
fi
