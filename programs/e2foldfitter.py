#!/bin/env python

from EMAN2 import *
from optparse import OptionParser
from math import *
import os
import sys
from Simplex import Simplex
from bisect import insort

cmp_probe=None
cmp_target=None
tdim=None
pdim=None
tdim2=None
pdim2=None
sfac=None
degrad=pi/180.0
ncmp=0

def compare(vec):
	"""Given an (alt,az,phi,x,y,z) vector, calculate the similarity
	of the probe to the map"""
	global cmp_probe,cmp_target,ncmp
	
#	print vec,pdim
#	print "\n%6.3f %6.3f %6.3f    %5.1f %5.1f %5.1f"%(vec[0],vec[1],vec[2],vec[3],vec[4],vec[5])
	a=cmp_target.get_rotated_clip(Transform((vec[3]+tdim[0]/2,vec[4]+tdim[1]/2,vec[5]+tdim[2]/2),(0,0,0),EULER_EMAN,vec[0],vec[1],vec[2]),pdim,1.0)
#	a.write_image("clip.mrc")
#	os.system("v2 clip.mrc")
	ncmp+=1
	return -cmp_probe.cmp("Dot",a,{})
	
def compares(vec):
	"""Given an (alt,az,phi,x,y,z) vector, calculate the similarity
	of the probe to the map"""
	global cmp_probe,cmp_target,sfac
	
	a=cmp_target.get_rotated_clip(Transform((vec[3]/float(sfac)+tdim2[0]/2,vec[4]/float(sfac)+tdim2[1]/2,vec[5]/float(sfac)+tdim2[2]/2),(0,0,0),EULER_EMAN,vec[0],vec[1],vec[2]),pdim2,1.0)
	return -cmp_probe.cmp("Dot",a,{})

def main():
	global tdim,pdim,tdim2,pdim2,sfac
	global cmp_probe,cmp_target
	progname = os.path.basename(sys.argv[0])
	usage = """Usage: %prog [options] target.mrc probe.mrc
	
Locates the best 'docking' locations for a small probe in a large target map. Note that the probe
should be in a box barely large enough for it. The target may be arbitrarily padded. For best speed
both box sizes should be multiples of 8."""

	parser = OptionParser(usage=usage,version=EMANVERSION)

	parser.add_option("--shrink", "-S", type="int", help="shrink factor for initial search, default=auto", default=0)
	parser.add_option("--epsilon","-E", type="float",help="final target accuracy, default=.01",default=.01)
	
	(options, args) = parser.parse_args()
	if len(args)<2 : parser.error("Input and output files required")
	try: chains=options.chains
	except: chains=None
	
	try : infile=open(args[0],"r")
	except : parser.error("Cannot open input file")
	
	# read the target and probe
	target=EMData()
	target.read_image(args[0])
	
	probe=EMData()
	probe.read_image(args[1])
	
	tdim=(target.get_xsize(),target.get_ysize(),target.get_zsize())
	pdim=(probe.get_xsize(),probe.get_ysize(),probe.get_zsize())
	
	if (pdim[0]>tdim[0] or pdim[1]>tdim[1] or pdim[2]>tdim[2]) :
		print "Probe must fit within target"
		exit(1)
	
	# shrink both by some factor which keeps the smallest axis of the probe at least 10 pixels
	# we'll have to reread the files if we want to recover the unscaled images
#	sfac=int(floor(min(pdim)/10.0))
	if options.shrink>0 : sfac=options.shrink
	else : sfac=int(floor(min(pdim)/12.0))
	print "Shrink by %d"%sfac
	target.mean_shrink(sfac)
	probe.mean_shrink(sfac)
	tdim2=(target.get_xsize(),target.get_ysize(),target.get_zsize())
	pdim2=(probe.get_xsize(),probe.get_ysize(),probe.get_zsize())
#	print (pdim2[0]-tdim2[0])/2,(pdim2[1]-tdim2[1])/2,(pdim2[2]-tdim2[2])/2,tdim2[0],tdim2[1],tdim2[2]
	probe.filter("normalize.edgemean")
	probeclip=probe.get_clip(Region((pdim2[0]-tdim2[0])/2,(pdim2[1]-tdim2[1])/2,(pdim2[2]-tdim2[2])/2,tdim2[0],tdim2[1],tdim2[2]))
	
	roughang=[(0,0),(45,0),(45,90),(45,180),(45,270),(90,0),(90,60),(90,120),(90,180),(90,240),(90,300),(135,0),(135,90),(135,180),(135,270),(180,0)]
#	roughang=[(0,0),(30,0),(30,90),(30,180),(30,270),(60,0),(60,45),(60,90),(60,135),(60,180),(60,225),(60,270),(60,315),
#	(90,0),(90,30),(90,60),(90,90),(90,120),(90,150),(90,180),(90,210),(90,240),(90,270),(90,300),(90,330),
#	(180,0),(150,0),(150,90),(150,180),(150,270),(120,0),(120,45),(120,90),(120,135),(120,180),(120,225),(120,270),(120,315)]

#	Log.logger().set_level(Log.LogLevel.DEBUG_LOG)
	
	print "Searching for candidate locations in reduced map"
	edge=max(pdim2)/2		# technically this should be max(pdim), but generally there is some padding in the probe model, and this is relatively harmless
	print "edge ",edge
	best=[]
	sum=probeclip.copy_head()
	sum.to_zero()
	for a1,a2 in roughang:
		for a3 in range(0,360,30):
			prr=probeclip.copy(0)
			prr.rotate(a1*degrad,a2*degrad,a3*degrad)
#			prr.write_image('prr.%0d%0d%0d.mrc'%(a1,a2,a3))
			
			ccf=target.calc_ccf(prr,1,None)
			mean=float(ccf.get_attr("mean"))
			sig=float(ccf.get_attr("sigma"))
			ccf.filter("mask.zeroedge3d",{"x0":edge,"x1":edge,"y0":edge,"y1":edge,"z0":edge,"z1":edge})
			sum+=ccf
			ccf.filter("mask.onlypeaks",{"npeaks":0})		# only look at peak values in the CCF map
			
#			ccf.write_image('ccf.%0d%0d%0d.mrc'%(a1,a2,a3))
			vec=ccf.calc_highest_locations(mean+sig+.0000001)
			for v in vec: best.append([v.value,a1*degrad,a2*degrad,a3*degrad,v.x-tdim2[0]/2,v.y-tdim2[1]/2,v.z-tdim2[2]/2,0])
			
#			print a1,a2,a3,mean+sig,float(ccf.get_attr("max")),len(vec)
	
	best.sort()		# this is a list of all reasonable candidate locations
	best.reverse()
	
	print len(best)," possible candidates"
	
	# this is designed to eliminate angular redundancies in peak location
#	print best[0]
#	print best[-1]
	
#	for i in best:
#		for j in best:
#			if (i[4]-j[4])**2+(i[5]-j[5])**2+(i[6]-j[6])**2>8.8 : continue
#			if j[0]>i[0] : i[7]=1
#	
#	best2=[]
#	for i in best:
#		if not i[7]: best2.append(i)

	# now we find peaks in the sum of all CCF calculations, and find the best angle associated with each peak
	sum.filter("mask.onlypeaks",{"npeaks":0})
	sum.write_image("sum.mrc")
	vec=sum.calc_highest_locations(mean+sig+.0000001)
	best2=[]
	for v in vec:
#		print "%5.1f  %5.1f  %5.1f"%(v.x*sfac-tdim[0]/2,v.y*sfac-tdim[1]/2,v.z*sfac-tdim[2]/2)
		for i in best:
			if i[4]+tdim2[0]/2==v.x and i[5]+tdim2[1]/2==v.y and i[6]+tdim2[2]/2==v.z :
				best2.append([i[0],i[1],i[2],i[3],i[4]*sfac,i[5]*sfac,i[6]*sfac,i[7]])
				break

	best2.sort()
	best2.reverse()
	print len(best2), " final candidates"
	print "Qual     \talt\taz\tphi\tdx\tdy\tdz\t"
	for i in best2: 
		print "%1.5f  \t%1.3f\t%1.3f\t%1.3f\t%1.1f\t%1.1f\t%1.1f"%(-i[0],i[1]/degrad,i[2]/degrad,i[3]/degrad,i[4],i[5],i[6])


	# try to improve the angles for each position
	print "\nOptimize each candidate in the reduced map with multiple angle trials"
	print "Qual     \talt\taz\tphi\tdx\tdy\tdz\t"
	cmp_target=target
	cmp_probe=probe
	for j in range(len(best2)):
		print j," --------"
		tries=[[0,0],[0,0],[0,0],[0,0]]
		testang=((0,0),(pi,0),(0,pi),(pi,pi))	# modify the 'best' angle a few times to try to find a better minimum
		for k in range(4):
			guess=best2[j][1:7]
			guess[0]+=testang[k][0]
			guess[1]+=testang[k][1]
			sm=Simplex(compares,guess,[1,1,1,.1,.1,.1])
			m=sm.minimize(monitor=0,epsilon=.01)
			tries[k][0]=m[1]
			tries[k][1]=m[0]
			print "%1.3f  \t%1.2f\t%1.2f\t%1.2f\t%1.1f\t%1.1f\t%1.1f"%(-tries[k][0],tries[k][1][0]/degrad,tries[k][1][1]/degrad,tries[k][1][2]/degrad,
				tries[k][1][3],tries[k][1][4],tries[k][1][5])
		best2[j][1:7]=min(tries)[1]		# best of the 4 angles we started with
		
	# reread the original images
	target.read_image(args[0])
	probe.read_image(args[1])
	cmp_target=target
	cmp_probe=probe
	
#	for i in best2:
#		c=probe.get_clip(Region((pdim[0]-tdim[0])/2,(pdim[1]-tdim[1])/2,(pdim[2]-tdim[2])/2,tdim[0],tdim[1],tdim[2]))
#		c.rotate_translate(*i[1:7])
#		c.write_image("z.%02d.mrc"%best2.index(i))
	
	print "Final optimization of each candidate"
	final=[]
	for j in range(len(best2)):
		sm=Simplex(compare,best2[j][1:7],[.5,.5,.5,2.,2.,2.])
		bt=sm.minimize(epsilon=options.epsilon)
		b=bt[0]
		print "\n%1.2f\t(%5.2f  %5.2f  %5.2f    %5.1f  %5.1f  %5.1f)"%(-bt[1],b[0]/degrad,b[1]/degrad,b[2]/degrad,b[3],b[4],b[5])
		final.append((bt[1],b))
	
	print "\n\nFinal Results"
	print "Qual     \talt\taz\tphi\tdx\tdy\tdz\t"
	out=open("foldfitter.out","w")
	final.sort()
	for i,j in enumerate(final):
		b=j[1]
		print "%d. %1.3f  \t%1.2f\t%1.2f\t%1.2f\t%1.1f\t%1.1f\t%1.1f"%(i,j[0],b[0]/degrad,b[1]/degrad,b[2]/degrad,b[3],b[4],b[5])
		out.write("%d. %1.3f  \t%1.2f\t%1.2f\t%1.2f\t%1.1f\t%1.1f\t%1.1f\n"%(i,j[0],b[0]/degrad,b[1]/degrad,b[2]/degrad,b[3],b[4],b[5]))
		a=cmp_target.get_rotated_clip(Transform((b[3]+tdim[0]/2,b[4]+tdim[1]/2,b[5]+tdim[2]/2),(0,0,0),EULER_EMAN,b[0],b[1],b[2]),pdim,1.0)
		a.write_image("clip.%02d.mrc"%i)
		pc=probe.get_clip(Region((pdim[0]-tdim[0])/2,(pdim[1]-tdim[1])/2,(pdim[2]-tdim[2])/2,tdim[0],tdim[1],tdim[2]))
		pc.rotate(-b[0],-b[2],-b[1])
		pc.rotate_translate(0,0,0,b[3],b[4],b[5])		# FIXME, when rotate_translate with post-translate works
#		pc.rotate_translate(-b[0],-b[2],-b[1],0,0,0,b[3],b[4],b[5])
		pc.write_image("final.%02d.mrc"%i)

	print ncmp," total comparisons"
	out.close()
	
#	print compare(best2[0][1:7])
	
#	print best2[0]
#	print best2[-1]
		
if __name__ == "__main__":
    main()
