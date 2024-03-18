#!/bin/bash
# check if python is installed
python --version &> /dev/null
if [ $? -ne 0 ]; then
  echo "ERROR: python not installed. Please install python and rerun this script."
fi
# add the script path to the bashrc
if [ "$(grep "FLITSR_HOME" ~/.bashrc)" == "" ]; then
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  echo "export FLITSR_HOME=\"$SCRIPT_DIR\"" >> ~/.bashrc
  echo "export PATH=\"\$FLITSR_HOME/bin:\$PATH\"" >> ~/.bashrc
fi
# install numpy
pip install numpy
