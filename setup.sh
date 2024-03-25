#!/bin/bash
# check if python is installed
python --version &> /dev/null
if [ $? -ne 0 ]; then
  echo "ERROR: python not installed. Please install python and rerun this script."
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
  line_num="$(grep -n "FLITSR_HOME" "$rcfile" | head -n1 | awk -F':' '{print $1-1}')"
  sed -i '/FLITSR_HOME/d' "$rcfile"
fi
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export FLITSR_HOME="$SCRIPT_DIR"
sed -i "${line_num}a export PATH=\"\$FLITSR_HOME/bin:\$PATH\"" "$rcfile"
sed -i "${line_num}a export PYTHONPATH=\"\$FLITSR_HOME:\$PYTHONPATH\"" "$rcfile"
sed -i "${line_num}a export FLITSR_HOME=\"$SCRIPT_DIR\"" "$rcfile"
echo "$rcfile has been updated. Run 'source $rcfile' to update your session."
# install numpy
python -m venv "$FLITSR_HOME/.venv"
source "$FLITSR_HOME/.venv/bin/activate"
pip install -r "$FLITSR_HOME/requirements.txt"
deactivate
