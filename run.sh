#!/bin/bash
#> hyb-group0-res.txt
#> hyb-group1-res.txt
#> hyb-group2-res.txt
#> hyb-group3-res.txt
#
#k=1;for i in `ls ../../results/convivaData/group0/*.out`; do python simulation.py $i >> hyb-group0-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
#k=1;for i in `ls ../../results/convivaData/group1/*.out`; do python simulation.py $i >> hyb-group1-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
#k=1;for i in `ls ../../results/convivaData/group2/*.out`; do  python simulation.py $i >> hyb-group2-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
#k=1;for i in `ls ../../results/convivaData/group3/*.out`; do  python simulation.py $i >> hyb-group3-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done

#k=1;for i in `ls ../../results/convivaData/group0/*.out`; do printf $i" " >> hyb-group0-res.txt; python simulation.py $i >> hyb-group0-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
#k=1;for i in `ls ../../results/convivaData/group1/*.out`; do printf $i" " >> hyb-group1-res.txt; python simulation.py $i >> hyb-group1-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
#k=1;for i in `ls ../../results/convivaData/group2/*.out`; do printf $i" " >> hyb-group2-res.txt; python simulation.py $i >> hyb-group2-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done
#k=1;for i in `ls ../../results/convivaData/group3/*.out`; do printf $i" " >> hyb-group3-res.txt; python simulation.py $i >> hyb-group3-res.txt; ((k++)); if [ $k -eq 10000 ]; then break; fi; done


#sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' hyb-group0-res.txt
#sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' hyb-group1-res.txt
#sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' hyb-group2-res.txt
#sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' hyb-group3-res.txt

path="../../results/convivaData/simulationComparison/atleast2min_group"
for i in `seq 1 6484`; do if [ ! -f $path/$i.out ]; then continue; fi; python simulation.py $path/$i.out; done


