#!/bin/sh
for i in $(awk -F "==" '{print $1}' requirements.txt)
do
     sudo pacman -S --needed python-$i --noconfirm
done
