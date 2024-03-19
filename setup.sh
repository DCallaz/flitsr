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
echo "$shell"
exit 0
if [ "$shell" == "bash" ]; then
  rcfile=~/.bashrc
elif [ "$shell" == "zsh" ]; then
  rcfile=~/.zshrc
else
  rcfile=~/.profile
fi
if [ "$(grep "FLITSR_HOME" "$rcfile")" == "" ]; then
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  echo "export FLITSR_HOME=\"$SCRIPT_DIR\"" >> "$rcfile"
  echo "export PATH=\"\$FLITSR_HOME/bin:\$PATH\"" >> "$rcfile"
  echo "$rcfile has been updated. Run 'source $rcfile' to update your session."
fi
# install numpy
pip install numpy
