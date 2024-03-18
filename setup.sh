#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "export FLITSR_HOME=\"$SCRIPT_DIR\"" >> ~/.bashrc
echo "export PATH=\"\$FLITSR_HOME/bin:\$PATH\"" >> ~/.bashrc
