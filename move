#!/bin/bash
#file=$1
if [ -z "$1" ] || [ "$1" == "tcm" ]; then
  proj=$(echo $PWD | cut -d/ -f7)
  for j in 1 2 4 8 16 32; do
    cd "$j-fault"
    for file in *.txt; do
      res=$(python3 ~/subjects/masters/feedback_localizer/find_unex.py "$file" num)
      if [ "$res" != "no faults found" ]; then
        mkdir -p "/home/dylan/subjects/masters/moved/$proj/$res-fault"
        cp "$file" "/home/dylan/subjects/masters/moved/$proj/$res-fault/$file"
      fi
    done
    cd ../
  done
else
  for version in *; do
    res=$(python3 $FLITSR_HOME/find_unex.py "$version" num "gzoltar")
    if [ "$res" != "no faults found" ]; then
      mkdir -p "moved/$res-fault"
      cp -r "$version" "moved/$res-fault/$version"
    fi
    #num=$(python3 -c "import sys;print(sys.argv[1].count('-'))" $version)
    #mkdir -p moved/$num"-fault"/
    #cp -r $version moved/$num"-fault"/$version
  done
fi
