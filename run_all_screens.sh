#!/bin/bash

echo "Current screen sessions:"
screen -ls
echo

launch_session() {
  name=$1
  dir=$2
  cmd=$3
  sleep_time=$4

  logfile="/dev/shm/${name}.log"

  if screen -list | grep -q "\.${name}"; then
    echo "Session '$name' already running."
  else
    echo "Starting '$name'..."
    screen -dmS "$name" bash -c "cd $dir && while true; do $cmd >> \"$logfile\" 2>&1; sleep $sleep_time; done"
    sleep 2
  fi
}

print_last_screen_output() {
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
launch_session gen_html /home/pi/energy/html/ "python3 generate_comed_html.py" 150
launch_session wemo /home/pi/energy "python3 wemoPlug-comed-old2.py" 300
launch_session awtrix3 /home/pi/energy/awtrix3/ "python3 send_price.py" 150
launch_session log_energy /home/pi/energy "python3 logEnergy.py" 300

echo
echo "Updated screen sessions:"
screen -ls

# Show last few lines of screen output
print_last_screen_output gen_html
print_last_screen_output wemo
print_last_screen_output awtrix3
print_last_screen_output log_energy
