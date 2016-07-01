#!/bin/bash
> bb-group0-res.txt
> bb-group1-res.txt
> bb-group2-res.txt
> bb-group3-res.txt

k=1;for i in `ls ../../results/convivaData/group0/*.out`; do printf $i" " >> bb-group0-res.txt; python simulation.py $i >> bb-group0-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
k=1;for i in `ls ../../results/convivaData/group1/*.out`; do printf $i" " >> bb-group1-res.txt; python simulation.py $i >> bb-group1-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
k=1;for i in `ls ../../results/convivaData/group2/*.out`; do printf $i" " >> bb-group2-res.txt; python simulation.py $i >> bb-group2-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
k=1;for i in `ls ../../results/convivaData/group3/*.out`; do printf $i" " >> bb-group3-res.txt; python simulation.py $i >> bb-group3-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done


sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group0-res.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group1-res.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group2-res.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' bb-group3-res.txt
