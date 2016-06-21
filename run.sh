#!/bin/bash
> bb-group0-res.txt
> bb-group1-res.txt
> bb-group2-res.txt
> bb-group3-res.txt

k=0;for i in `ls ../../results/convivaData/group0/*.out`; do printf "$k "; python simulation.py $i; ((k++)); if [ $k -eq 10 ]; then break; fi; done >> bb-group0-res.txt
k=0;for i in `ls ../../results/convivaData/group1/*.out`; do printf "$k "; python simulation.py $i; ((k++)); if [ $k -eq 10 ]; then break; fi; done >> bb-group1-res.txt
k=0;for i in `ls ../../results/convivaData/group2/*.out`; do printf "$k "; python simulation.py $i; ((k++)); if [ $k -eq 10 ]; then break; fi; done >> bb-group2-res.txt
k=0;for i in `ls ../../results/convivaData/group3/*.out`; do printf "$k "; python simulation.py $i; ((k++)); if [ $k -eq 10 ]; then break; fi; done >> bb-group3-res.txt


sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group0-res.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group1-res.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group2-res.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group3-res.txt
