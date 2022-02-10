#!/bin/bash
#file=$1
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
