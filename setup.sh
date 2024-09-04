#!/bin/bash
# check if python is installed
python --version &> /dev/null
if [ $? -ne 0 ]; then
  echo "ERROR: python not installed. Please install python and rerun this script."
  exit 1
fi
# add the script path to the bashrc/zshrc
shell="$(ps -p$PPID | grep -v "PID" | awk '{print $4}')"
if [[ ! "$shell" =~ ^sh|csh|tcsh|ksh|dash|bash|zsh|fish$ ]]; then
  shell="$(basename $SHELL)"
fi
if [ "$shell" == "bash" ]; then
  rcfile=~/.bashrc
elif [ "$shell" == "zsh" ]; then
  rcfile=~/.zshrc
else
  rcfile=~/.profile
fi
if [ ! -f "$rcfile" ]; then
  echo "# FLITSR setup" > "$rcfile"
fi
line_num="$(wc -l "$rcfile" | awk '{print $1}')"
if [ "$(grep "FLITSR_HOME" "$rcfile")" != "" ]; then
  lines=($(grep -n "FLITSR_HOME" "$rcfile" | sed -e 1b -e '$!d' | awk -F':' '{print $1}'))
  sed -i "${lines[0]},${lines[1]}d" "$rcfile"
  line_num="$((${lines[0]}-1))"
fi
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export FLITSR_HOME="$SCRIPT_DIR"
sed -i "${line_num}a export PATH=\"\${PATH:+\$PATH:}\$FLITSR_HOME/bin\"" "$rcfile"
sed -i "${line_num}a export PYTHONPATH=\"\${PYTHONPATH:+\$PYTHONPATH:}\$FLITSR_HOME\"" "$rcfile"
sed -i "${line_num}a export FLITSR_HOME=\"$SCRIPT_DIR\"" "$rcfile"
echo "$rcfile has been updated. Run 'source $rcfile' to update your session."
# install virtual environment
python -m venv "$FLITSR_HOME/.venv"
source "$FLITSR_HOME/.venv/bin/activate"
pip install -r "$FLITSR_HOME/requirements.txt"
deactivate
