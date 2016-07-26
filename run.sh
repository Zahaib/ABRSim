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

#path="../../results/convivaData/simulationComparison/manual_group"
#for i in `ls $path/*.txt | sort -n`; do python simulation.py $i; done

#export fn=$1
#export k=1
#function output () {
#  ((k++))
#  l=$(sed -n "${k}p" $fn)
#    echo $l
#}
#
#export -f output
#parallel --jobs 8 output ::: 4
  
#function simulate() {
#  while read line; do
#    export line
#    python simulation.py $line >> pub1.txt
#  done < $1
#}

> pub1.txt
parallel -j 48 -a filelist.txt python simulation.py >> pub1.txt
sed -i 's/QoE: //g; s/ avg. bitrate://g; s/ buf. ratio://g; s/ optimal A://g' pub1.txt 
