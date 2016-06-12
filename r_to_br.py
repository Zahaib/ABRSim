import matplotlib, re
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, sys, glob, re, math, operator, random, commands
import numpy as np

def generate_file(f, r, t):
	randomness = 0#0.05
	fo = open(f, "w")
	for i in range(t):
		random_ = 2*(random.random() - 0.5)*randomness
		fo.write(str(i*1000) + " " + str(r*(1+random_)) + "\n")
	fo.close()

duration = int(sys.argv[1])
x = []
y1 = []
y2 = []
r_s = 350
r_e = 10000
step = 50
for i in range(r_s, r_e, step):
	if i%100 == 0:
		print i
	generate_file("temp", i, duration)
	o = commands.getstatusoutput("python simulation.py temp")
	g = re.match("maxQoE: (.*) avg. bitrate: (.*) buf. ratio: (.*) numSwtiches: (.*)", o[1])
	x.append(i)
	y1.append(float(g.group(2)))
	y2.append(float(g.group(1)))

fig = plt.figure()
ax = fig.add_subplot(111)
ax2 = ax.twinx()

print y1
print y2

ax.plot(x, y1, "-bx")
ax.plot([-1,-1],[-1,-1], "--r")
ax2.plot(x, y2, "--r")
ax.legend(["avg. bitrate", "maxQoE"], 4)
#ax2.legend(["maxQoE"], 4)
ax.grid()
ax.set_xlim([r_s, r_e])
ax.set_ylim([0, 4800])
#ax[i].legend(le[i],fontsize=legend_font_size)
#ax[i].set_ylabel("++", fontsize=label_font_size)
ax.set_ylabel("Avg Bitrate (b/s)")
ax2.set_ylabel("maxQoE")
ax.set_xlabel("Maintained Rate (b/s)")

textstr = "bitrates candidate:\n350\n700\n1200\n2400\n4800"
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.65, 0.4, textstr, transform=ax.transAxes, verticalalignment='top', fontsize=14, bbox=props)

plt.tight_layout()
plt.savefig("r_to_br_%s.png"%(duration))
