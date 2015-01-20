#!/usr/bin/env python

#
# Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
# Copyright (c) 2000-2006 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

# $Id$
import	global_def
from	global_def 	import *
from	EMAN2 		import EMUtil, parsemodopt, EMAN2Ctf
from    EMAN2jsondb import js_open_dict

from	utilities 	import *
from statistics import mono

""" Traveling salesman problem solved using Simulated Annealing.
"""
from scipy import *
from pylab import *

def Distance(im1, im2, lccc):
	i1=im1.get_attr("ID")
	i2=im2.get_attr("ID")
	
	return lccc[mono(i1,i2)][0]
# 	return sqrt((R1[0]-R2[0])**2+(R1[1]-R2[1])**2)

def TotalDistance(city, R, lccc):
    dist=0
    for i in range(len(city)-1):
        dist += Distance(R[city[i]],R[city[i+1]], lccc)
    dist += Distance(R[city[-1]],R[city[0]], lccc)
    return dist
    
def reverse(city, n):
    nct = len(city)
    nn = (1+ ((n[1]-n[0]) % nct))/2 # half the lenght of the segment to be reversed
    # the segment is reversed in the following way n[0]<->n[1], n[0]+1<->n[1]-1, n[0]+2<->n[1]-2,...
    # Start at the ends of the segment and swap pairs of cities, moving towards the center.
    for j in range(nn):
        k = (n[0]+j) % nct
        l = (n[1]-j) % nct
        (city[k],city[l]) = (city[l],city[k])  # swap
    
def transpt(city, n):
    nct = len(city)
    
    newcity=[]
    # Segment in the range n[0]...n[1]
    for j in range( (n[1]-n[0])%nct + 1):
        newcity.append(city[ (j+n[0])%nct ])
    # is followed by segment n[5]...n[2]
    for j in range( (n[2]-n[5])%nct + 1):
        newcity.append(city[ (j+n[5])%nct ])
    # is followed by segment n[3]...n[4]
    for j in range( (n[4]-n[3])%nct + 1):
        newcity.append(city[ (j+n[3])%nct ])
    return newcity

def Plot(city, R, dist):
    # Plot
    Pt = [R[city[i]] for i in range(len(city))]
    Pt += [R[city[0]]]
    Pt = array(Pt)
    title('Total distance='+str(dist))
    plot(Pt[:,0], Pt[:,1], '-o')
    show()

def tsp(stack, lccc):

#     ncity = 100        # Number of cities to visit
    ncity = len(stack)        # Number of cities to visit
    maxTsteps = 100    # Temperature is lowered not more than maxTsteps
    Tstart = 0.2       # Starting temperature - has to be high enough
    fCool = 0.9        # Factor to multiply temperature at each cooling step
    maxSteps = 100*ncity     # Number of steps at constant temperature
    maxAccepted = 10*ncity   # Number of accepted steps at constant temperature

    Preverse = 0.5      # How often to choose reverse/transpose trial move

    # Choosing city coordinates
    R=[]  # coordinates of cities are choosen randomly
    for i in range(ncity):
#         R.append( [rand(),rand()] )
        R.append( stack[i] )
    R = array(R)
            

    # The index table -- the order the cities are visited.
    city = range(ncity)
    # Distance of the travel at the beginning
    dist = TotalDistance(city, R, lccc)

    # Stores points of a move
    n = zeros(6, dtype=int)
    nct = len(R) # number of cities
    
    T = Tstart # temperature

#     Plot(city, R, dist)
    
    for t in range(maxTsteps):  # Over temperature

        accepted = 0
        for i in range(maxSteps): # At each temperature, many Monte Carlo steps
            
            while True: # Will find two random cities sufficiently close by
                # Two cities n[0] and n[1] are choosen at random
                n[0] = int((nct)*rand())     # select one city
                n[1] = int((nct-1)*rand())   # select another city, but not the same
                if (n[1] >= n[0]): n[1] += 1   #
                if (n[1] < n[0]): (n[0],n[1]) = (n[1],n[0]) # swap, because it must be: n[0]<n[1]
                nn = (n[0]+nct -n[1]-1) % nct  # number of cities not on the segment n[0]..n[1]
                if nn>=3: break
        
            # We want to have one index before and one after the two cities
            # The order hence is [n2,n0,n1,n3]
            n[2] = (n[0]-1) % nct  # index before n0  -- see figure in the lecture notes
            n[3] = (n[1]+1) % nct  # index after n2   -- see figure in the lecture notes
            
            if Preverse > rand(): 
                # Here we reverse a segment
                # What would be the cost to reverse the path between city[n[0]]-city[n[1]]?
                de = Distance(R[city[n[2]]],R[city[n[1]]], lccc) + Distance(R[city[n[3]]],R[city[n[0]]], lccc) - Distance(R[city[n[2]]],R[city[n[0]]], lccc) - Distance(R[city[n[3]]],R[city[n[1]]], lccc)
                
                if de<0 or exp(-de/T)>rand(): # Metropolis
                    accepted += 1
                    dist += de
                    reverse(city, n)
            else:
                # Here we transpose a segment
                nc = (n[1]+1+ int(rand()*(nn-1)))%nct  # Another point outside n[0],n[1] segment. See picture in lecture nodes!
                n[4] = nc
                n[5] = (nc+1) % nct
        
                # Cost to transpose a segment
                de = -Distance(R[city[n[1]]],R[city[n[3]]], lccc) - Distance(R[city[n[0]]],R[city[n[2]]], lccc) - Distance(R[city[n[4]]],R[city[n[5]]], lccc)
                de += Distance(R[city[n[0]]],R[city[n[4]]], lccc) + Distance(R[city[n[1]]],R[city[n[5]]], lccc) + Distance(R[city[n[2]]],R[city[n[3]]], lccc)
                
                if de<0 or exp(-de/T)>rand(): # Metropolis
                    accepted += 1
                    dist += de
                    city = transpt(city, n)
                    
            if accepted > maxAccepted: break

        # Plot
#         Plot(city, R, dist)
            
        print "T=%10.5f , distance= %10.5f , accepted steps= %d" %(T, dist, accepted)
        T *= fCool             # The system is cooled down
        if accepted == 0: break  # If the path does not want to change any more, we can stop

        
#     Plot(city, R, dist)
	return city


def main():
	import sys
	import os
	import math
	import random
	import pyemtbx.options
	import time
	from   random   import random, seed, randint
	from   optparse import OptionParser

	progname = os.path.basename(sys.argv[0])
	usage = progname + """ [options] <inputfile> <outputfile>

	Generic 2-D image processing programs.

	Functionality:

	1.  Phase flip a stack of images and write output to new file:
	sxprocess.py input_stack.hdf output_stack.hdf --phase_flip
	
	2.  Resample (decimate or interpolate up) images (2D or 3D) in a stack to change the pixel size.
	    The window size will change accordingly.
	sxprocess input.hdf output.hdf  --changesize --ratio=0.5

	3.  Compute average power spectrum of a stack of 2D images with optional padding (option wn) with zeroes.
	sxprocess.py input_stack.hdf powerspectrum.hdf --pw [--wn=1024]

	4.  Order a 2-D stack of image based on pair-wise similarity (computed as a cross-correlation coefficent).
	    There are three ways to use the program
	   4.1  Use option initial to specify which image will be used as an initial seed to form the chain.
	        sxprocess.py input_stack.hdf output_stack.hdf --order  --initial=23 --radius=25
	   4.2  If options initial is omitted, the program will determine which image best serves as initial seed to form the chain
	        sxprocess.py input_stack.hdf output_stack.hdf --order  --radius=25
	   4.3  Use option circular to form a circular chain.
	        sxprocess.py input_stack.hdf output_stack.hdf --order  --circular--radius=25

	5.  Generate a stack of projections bdb:data and micrographs with prefix mic (i.e., mic0.hdf, mic1.hdf etc) from structure input_structure.hdf, with CTF applied to both projections and micrographs:
	sxprocess.py input_structure.hdf data mic --generate_projections format="bdb":apix=5.2:CTF=True:boxsize=64

    6.  Retrieve original image numbers in the selected ISAC group (here group 12 from generation 3):
    sxprocess.py  bdb:test3 class_averages_generation_3.hdf  list3_12.txt --isacgroup=12 --params=myid

    7.  Adjust rotationally averaged power spectrum of an image to that of a reference image or a reference 1D power spectrum stored in an ASCII file.
    	Optionally use a tangent low-pass filter.  Also works for a stack of images, in which case the output is also a stack.
    sxprocess.py  vol.hdf ref.hdf  avol.hdf < 0.25 0.2> --adjpw
    sxprocess.py  vol.hdf pw.txt   avol.hdf < 0.25 0.2> --adjpw

	8.  Generate a 1D rotationally averaged power spectrum of an image.
    sxprocess.py  vol.hdf --rotwp=rotpw.txt
    # Output will contain three columns:
       (1) integer line number (from zero to approximately to half the image size)
       (2) rotationally averaged power spectrum
       (3) logarithm of the rotationally averaged power spectrum

	9.  Import ctf parameters from the output of sxcter into windowed particle headers.
	    There are three possible input files formats:  (1) all particles are in one stack, (2 aor 3) particles are in stacks, each stack corresponds to a single micrograph.
	    In each case the particles should contain a name of the micrograph of origin stores using attribute name 'ptcl_source_image'.  Normally this is done by e2boxer.py during windowing.
	    Particles whose defocus or astigmatism error exceed set thresholds will be skipped, otherwise, virtual stacks with the original way preceded by G will be created.
	sxprocess.py  --input=bdb:data  --importctf=outdir/partres  --defocuserror=10.0  --astigmatismerror=5.0
	#  Output will be a vritual stack bdb:Gdata
	sxprocess.py  --input="bdb:directory/stacks*"  --importctf=outdir/partres  --defocuserror=10.0  --astigmatismerror=5.0
	To concatenate output files:
	cd directory
	e2bdb.py . --makevstack=bdb:allparticles  --filt=G
	IMPORTANT:  Please do not move (or remove!) any input/intermediate EMAN2DB files as the information is linked between them.

"""

	parser = OptionParser(usage,version=SPARXVERSION)
	parser.add_option("--order", action="store_true", help="Two arguments are required: name of input stack and desired name of output stack. The output stack is the input stack sorted by similarity in terms of cross-correlation coefficent.", default=False)
	parser.add_option("--order_lookup", action="store_true", help="Test/Debug.", default=False)
	parser.add_option("--order_metropolis", action="store_true", help="Test/Debug.", default=False)
	parser.add_option("--initial", type="int", default=-1, help="Specifies which image will be used as an initial seed to form the chain. (default = 0, means the first image)")
	parser.add_option("--circular", action="store_true", help="Select circular ordering (fisr image has to be similar to the last", default=False)
	parser.add_option("--radius", type="int", default=-1, help="Radius of a circular mask for similarity based ordering")
	parser.add_option("--changesize", action="store_true", help="resample (decimate or interpolate up) images (2D or 3D) in a stack to change the pixel size.", default=False)
	parser.add_option("--ratio", type="float", default=1.0, help="The ratio of new to old image size (if <1 the pixel size will increase and image size decrease, if>1, the other way round")
	parser.add_option("--pw", action="store_true", help="compute average power spectrum of a stack of 2-D images with optional padding (option wn) with zeroes", default=False)
	parser.add_option("--wn", type="int", default=-1, help="Size of window to use (should be larger/equal than particle box size, default padding to max(nx,ny))")
	parser.add_option("--phase_flip", action="store_true", help="Phase flip the input stack", default=False)
	parser.add_option("--makedb", metavar="param1=value1:param2=value2", type="string",
					action="append",  help="One argument is required: name of key with which the database will be created. Fill in database with parameters specified as follows: --makedb param1=value1:param2=value2, e.g. 'gauss_width'=1.0:'pixel_input'=5.2:'pixel_output'=5.2:'thr_low'=1.0")
	parser.add_option("--generate_projections", metavar="param1=value1:param2=value2", type="string",
					action="append", help="Three arguments are required: name of input structure from which to generate projections, desired name of output projection stack, and desired prefix for micrographs (e.g. if prefix is 'mic', then micrographs mic0.hdf, mic1.hdf etc will be generated). Optional arguments specifying format, apix, box size and whether to add CTF effects can be entered as follows after --generate_projections: format='bdb':apix=5.2:CTF=True:boxsize=100, or format='hdf', etc., where format is bdb or hdf, apix (pixel size) is a float, CTF is True or False, and boxsize denotes the dimension of the box (assumed to be a square). If an optional parameter is not specified, it will default as follows: format='bdb', apix=2.5, CTF=False, boxsize=64.")
	parser.add_option("--isacgroup", type="int", help="Retrieve original image numbers in the selected ISAC group   See ISAC documentaion for details.", default=-1)
	parser.add_option("--params",	   type="string",       default=None,    help="Name of header of parameter, which one depends on specific option")
	parser.add_option("--adjpw", action="store_true", help="Adjust rotationally averaged power spectrum of an image", default=False)
	parser.add_option("--rotpw", type="string",   default=None,    help="Name of the text file to contain rotationally averaged power spectrum of the input image.")

	
	# import ctf estimates done using cter
	parser.add_option("--input",              type="string",	default= None,     		  help="Input particles.")
	parser.add_option("--importctf",          type="string",	default= None,     		  help="Name of the file containing CTF parameters produced by sxcter.")
	parser.add_option("--defocuserror",       type="float",  	default=1000000.0,        help="Exclude micrographs whose relative defocus error as estimated by sxcter is larger than defocuserror percent.  The error is computed as (std dev defocus)/defocus*100%")
	parser.add_option("--astigmatismerror",   type="float",  	default=360.0,            help="Set to zero astigmatism for micrographs whose astigmatism angular error as estimated by sxcter is larger than astigmatismerror degrees.")


 	(options, args) = parser.parse_args()

	global_def.BATCH = True

	if options.order:
		nargs = len(args)
		if nargs != 2:
			print "must provide name of input and output file!"
			return
		
		from utilities import get_params2D, model_circle
		from fundamentals import rot_shift2D
		from statistics import ccc
		from time import time
		from alignment import align2d
		from multi_shc import mult_transform 
		
		stack = args[0]
		new_stack = args[1]
		
		d = EMData.read_images(stack)
		try:
			ttt = d[0].get_attr('xform.params2d')
			for i in xrange(len(d)):
				alpha, sx, sy, mirror, scale = get_params2D(d[i])
				d[i] = rot_shift2D(d[i], alpha, sx, sy, mirror)
		except:
			pass

		nx = d[0].get_xsize()
		ny = d[0].get_ysize()
		if options.radius < 1 : radius = nx//2-2
		else:  radius = options.radius
		mask = model_circle(radius, nx, ny)

		init = options.initial
		
		if init > -1 :
			temp = d[init].copy()
			temp.write_image(new_stack, 0)
			del d[init]
			k = 1
			lsum = 0.0
			while len(d) > 1:
				maxcit = -111.
				for i in xrange(len(d)):
						cuc = ccc(d[i], temp, mask)
						if cuc > maxcit:
								maxcit = cuc
								qi = i
				# 	print k, maxcit
				lsum += maxcit
				temp = d[qi].copy()
				del d[qi]
				temp.write_image(new_stack, k)
				k += 1
			print  lsum
			d[0].write_image(new_stack, k)
		else:			
			if options.circular :
				#  figure the "best circular" starting image
				maxsum = -1.023
				for m in xrange(len(d)):
					indc = range(len(d) )
					lsnake = [-1]*(len(d)+1)
					lsnake[0]  = m
					lsnake[-1] = m
					del indc[m]
					temp = d[m].copy()
					lsum = 0.0
					direction = +1
					k = 1
					while len(indc) > 1:
						maxcit = -111.
						for i in xrange(len(indc)):
								cuc = ccc(d[indc[i]], temp, mask)
								if cuc > maxcit:
										maxcit = cuc
										qi = indc[i]
						lsnake[k] = qi
						lsum += maxcit
						del indc[indc.index(qi)]
						direction = -direction
						for i in xrange( 1,len(d) ):
							if( direction > 0 ):
								if(lsnake[i] == -1):
									temp = d[lsnake[i-1]].copy()
									#print  "  forw  ",lsnake[i-1]
									k = i
									break
							else:
								if(lsnake[len(d) - i] == -1):
									temp = d[lsnake[len(d) - i +1]].copy()
									#print  "  back  ",lsnake[len(d) - i +1]
									k = len(d) - i
									break

					lsnake[lsnake.index(-1)] = indc[-1]
					#print  " initial image and lsum  ",m,lsum
					#print lsnake
					if(lsum > maxsum):
						maxsum = lsum
						init = m
						snake = [lsnake[i] for i in xrange(len(d))]
				print  "  Initial image selected : ",init,maxsum
				print lsnake
				for m in xrange(len(d)):  d[snake[m]].write_image(new_stack, m)
			else:
				#  figure the "best" starting image
				maxsum = -1.023
				for m in xrange(len(d)):
					indc = range(len(d) )
					lsnake = [m]
					del indc[m]
					temp = d[m].copy()
					lsum = 0.0
					while len(indc) > 1:
						maxcit = -111.
						for i in xrange(len(indc)):
								cuc = ccc(d[indc[i]], temp, mask)
								if cuc > maxcit:
										maxcit = cuc
										qi = indc[i]
						lsnake.append(qi)
						lsum += maxcit
						temp = d[qi].copy()
						del indc[indc.index(qi)]

					lsnake.append(indc[-1])
					#print  " initial image and lsum  ",m,lsum
					#print lsnake
					if(lsum > maxsum):
						maxsum = lsum
						init = m
						snake = [lsnake[i] for i in xrange(len(d))]
				print  "  Initial image selected : ",init,maxsum
				print lsnake
				for m in xrange(len(d)):  d[snake[m]].write_image(new_stack, m)
					
	if options.order_lookup:
		nargs = len(args)
		if nargs != 2:
			print "must provide name of input and output file!"
			return
		
		print "Using Lookup Table"
		from utilities import get_params2D, model_circle
		from fundamentals import rot_shift2D
		from statistics import ccc
		from time import time
		from alignment import align2d
		from multi_shc import mult_transform 
		
		stack = args[0]
		new_stack = args[1]
		
		d = EMData.read_images(stack)
		try:
			ttt = d[0].get_attr('xform.params2d')
			for i in xrange(len(d)):
				alpha, sx, sy, mirror, scale = get_params2D(d[i])
				d[i] = rot_shift2D(d[i], alpha, sx, sy, mirror)
		except:
			pass

		nx = d[0].get_xsize()
		ny = d[0].get_ysize()
		if options.radius < 1 : radius = nx//2-2
		else:  radius = options.radius
		mask = model_circle(radius, nx, ny)
		
		from statistics import mono
		lend=len(d)
		lccc=[None]*(lend*(lend-1)/2)

		for i in xrange(lend):				
			for j in xrange(i+1, lend):
				alpha, sx, sy, mir, peak = align2d(d[i],d[j], xrng=3, yrng=3, step=1, first_ring=1, last_ring=radius, mode = "F")
				T = Transform({"type":"2D","alpha":alpha,"tx":sx,"ty":sy,"mirror":mir,"scale":1.0})

				lccc[mono(i,j)] = [ccc(d[j], rot_shift2D(d[i], alpha, sx, sy, mir, 1.0), mask), T]
		
		maxsum = -1.023
		for m in xrange(len(d)):
			indc = range(len(d) )
			lsnake = [m]
			del indc[m]

			lsum = 0.0
			while len(indc) > 1:
				maxcit = -111.
				for i in xrange(len(indc)):
						cuc = lccc[mono(indc[i], lsnake[-1])][0]
						if cuc > maxcit:
								maxcit = cuc
								qi = indc[i]
				lsnake.append(qi)
				lsum += maxcit

				del indc[indc.index(qi)]

			lsnake.append(indc[-1])
			#print  " initial image and lsum  ",m,lsum
			#print lsnake
			if(lsum > maxsum):
				maxsum = lsum
				init = m
				snake = [lsnake[i] for i in xrange(len(d))]
		print  "  Initial image selected : ",init,maxsum
		print snake
		
		ltrans=[Transform()]*len(d)
		
		# this is not what I dictated you.
		for m in xrange(1,len(d)):
			ltrans[m] = lccc[mono(snake[m-1], snake[m])][1]*ltrans[m-1]

		for m in xrange(1,len(d)):
			prms = ltrans[m].get_params("2D")
			d[m] = rot_shift2D(d[m], prms["alpha"], prms["tx"], prms["ty"], prms["mirror"], prms["scale"])
		
		for m in xrange(len(d)):  d[snake[m]].write_image(new_stack, m)

	if options.order_metropolis:
		nargs = len(args)
		if nargs != 2:
			print "must provide name of input and output file!"
			return
		
		print "Using Metropolis Algorithm"
		from utilities import get_params2D, model_circle
		from fundamentals import rot_shift2D
		from statistics import ccc
		from time import time
		from alignment import align2d
		from multi_shc import mult_transform 
		
		stack = args[0]
		new_stack = args[1]
		
		d = EMData.read_images(stack)
		try:
			ttt = d[0].get_attr('xform.params2d')
			for i in xrange(len(d)):
				alpha, sx, sy, mirror, scale = get_params2D(d[i])
				d[i] = rot_shift2D(d[i], alpha, sx, sy, mirror)
		except:
			pass

		nx = d[0].get_xsize()
		ny = d[0].get_ysize()
		if options.radius < 1 : radius = nx//2-2
		else:  radius = options.radius
		mask = model_circle(radius, nx, ny)
		
		from statistics import mono
		lend=len(d)
		lccc=[None]*(lend*(lend-1)/2)
		
		for i in xrange(lend):				
			for j in xrange(i+1, lend):
				alpha, sx, sy, mir, peak = align2d(d[i],d[j], xrng=3, yrng=3, step=1, first_ring=1, last_ring=radius, mode = "F")
				T = Transform({"type":"2D","alpha":alpha,"tx":sx,"ty":sy,"mirror":mir,"scale":1.0})

				lccc[mono(i,j)] = [1.0-ccc(d[j], rot_shift2D(d[i], alpha, sx, sy, mir, 1.0), mask), T]

		snake = tsp(d, lccc)
		print snake
	
		
	if options.phase_flip:
		nargs = len(args)
		if nargs != 2:
			print "must provide name of input and output file!"
			return
		from EMAN2 import Processor
		instack = args[0]
		outstack = args[1]
		nima = EMUtil.get_image_count(instack)
		from filter import filt_ctf
		for i in xrange(nima):
			img = EMData()
			img.read_image(instack, i)
			try:
				ctf = img.get_attr('ctf')
			except:
				print "no ctf information in input stack! Exiting..."
				return
			
			dopad = True
			sign = 1
			binary = 1  # phase flip
				
			assert img.get_ysize() > 1	
			dict = ctf.to_dict()
			dz = dict["defocus"]
			cs = dict["cs"]
			voltage = dict["voltage"]
			pixel_size = dict["apix"]
			b_factor = dict["bfactor"]
			ampcont = dict["ampcont"]
			dza = dict["dfdiff"]
			azz = dict["dfang"]
			
			if dopad and not img.is_complex(): ip = 1
			else:                             ip = 0
	
	
			params = {"filter_type": Processor.fourier_filter_types.CTF_,
	 			"defocus" : dz,
				"Cs": cs,
				"voltage": voltage,
				"Pixel_size": pixel_size,
				"B_factor": b_factor,
				"amp_contrast": ampcont,
				"dopad": ip,
				"binary": binary,
				"sign": sign,
				"dza": dza,
				"azz":azz}
			
			tmp = Processor.EMFourierFilter(img, params)
			tmp.set_attr_dict({"ctf": ctf})
			
			tmp.write_image(outstack, i)

	if options.changesize:
		nargs = len(args)
		if nargs != 2:
			ERROR("must provide name of input and output file!", "change size", 1)
			return
		from utilities import get_im
		instack = args[0]
		outstack = args[1]
		sub_rate = float(options.ratio)
			
		nima = EMUtil.get_image_count(instack)
		from fundamentals import resample
		for i in xrange(nima):
			resample(get_im(instack, i), sub_rate).write_image(outstack, i)

	if options.isacgroup>-1:
		nargs = len(args)
		if nargs != 3:
			ERROR("Three files needed on input!", "isacgroup", 1)
			return
		from utilities import get_im
		instack = args[0]
		m=get_im(args[1],int(options.isacgroup)).get_attr("members")
		l = []
		for k in m:
			l.append(int(get_im(args[0],k).get_attr(options.params)))
		from utilities import write_text_file
		write_text_file(l, args[2])

	if options.pw:
		nargs = len(args)
		if nargs != 2:
			ERROR("must provide name of input and output file!", "pw", 1)
			return
		from utilities import get_im
		d = get_im(args[0])
		nx = d.get_xsize()
		ny = d.get_ysize()
		wn = int(options.wn)
		if wn == -1:
			wn = max(nx, ny)
		else:
			if( (wn<nx) or (wn<ny) ):  ERROR("window size cannot be smaller than the image size","pw",1)
		n = EMUtil.get_image_count(args[0])
		from utilities import model_blank, pad
		from EMAN2 import periodogram
		p = model_blank(wn,wn)
		for i in xrange(n):
			d = get_im(args[0], i)
			st = Util.infomask(d, None, True)
			d -= st[0]
			p += periodogram(pad(d, wn, wn, 1, 0.))
		p /= n
		p.write_image(args[1])
		sys.exit()

	if options.adjpw:

		if len(args) < 3:
			ERROR("filt_by_rops input target output fl aa (the last two are optional parameters of a low-pass filter)","adjpw",1)
			return
		img_stack = args[0]
		from math         import sqrt
		from fundamentals import rops_table, fft
		from utilities    import read_text_file, get_im
		from filter       import  filt_tanl, filt_table
		if(  args[1][-3:] == 'txt'):
			rops_dst = read_text_file( args[1] )
		else:
			rops_dst = rops_table(get_im( args[1] ))

		out_stack = args[2]
		if(len(args) >4):
			fl = float(args[3])
			aa = float(args[4])
		else:
			fl = -1.0
			aa = 0.0

		nimage = EMUtil.get_image_count( img_stack )

		for i in xrange(nimage):
			img = fft(get_im(img_stack, i) )
			rops_src = rops_table(img)

			assert len(rops_dst) == len(rops_src)

			table = [0.0]*len(rops_dst)
			for j in xrange( len(rops_dst) ):
				table[j] = sqrt( rops_dst[j]/rops_src[j] )

			if( fl > 0.0):
				img = filt_tanl(img, fl, aa)
			img = fft(filt_table(img, table))
			img.write_image(out_stack, i)

	if options.rotpw != None:

		if len(args) != 1:
			ERROR("Only one input permitted","rotpw",1)
			return
		from utilities import write_text_file, get_im
		from fundamentals import rops_table
		from math import log10
		t = rops_table(get_im(args[0]))
		x = range(len(t))
		r = [0.0]*len(x)
		for i in x:  r[i] = log10(t[i])
		write_text_file([x,t,r],options.rotpw)


	if options.makedb != None:
		nargs = len(args)
		if nargs != 1:
			print "must provide exactly one argument denoting database key under which the input params will be stored"
			return
		dbkey = args[0]
		print "database key under which params will be stored: ", dbkey
		gbdb = js_open_dict("e2boxercache/gauss_box_DB.json")
				
		parmstr = 'dummy:'+options.makedb[0]
		(processorname, param_dict) = parsemodopt(parmstr)
		dbdict = {}
		for pkey in param_dict:
			if (pkey == 'invert_contrast') or (pkey == 'use_variance'):
				if param_dict[pkey] == 'True':
					dbdict[pkey] = True
				else:
					dbdict[pkey] = False
			else:		
				dbdict[pkey] = param_dict[pkey]
		gbdb[dbkey] = dbdict

	if options.generate_projections:
		nargs = len(args)
		if nargs != 3:
			print "Must provide name of input structure from which to generate projections, desired name of output projection stack, and desired prefix for output micrographs. Exiting..."
			return
		inpstr = args[0]
		outstk = args[1]
		micpref = args[2]

		parmstr = 'dummy:'+options.generate_projections[0]
		(processorname, param_dict) = parsemodopt(parmstr)

		parm_CTF = False
		parm_format = 'bdb'
		parm_apix = 2.5

		if 'CTF' in param_dict:
			if param_dict['CTF'] == 'True':
				parm_CTF = True

		if 'format' in param_dict:
			parm_format = param_dict['format']

		if 'apix' in param_dict:
			parm_apix = float(param_dict['apix'])

		boxsize = 64
		if 'boxsize' in param_dict:
			boxsize = int(param_dict['boxsize'])

		print "pixel size: ", parm_apix, " format: ", parm_format, " add CTF: ", parm_CTF, " box size: ", boxsize

		scale_mult = 2500
		sigma_add = 1.5
		sigma_proj = 30.0
		sigma2_proj = 17.5
		sigma_gauss = 0.3
		sigma_mic = 30.0
		sigma2_mic = 17.5
		sigma_gauss_mic = 0.3
		
		if 'scale_mult' in param_dict:
			scale_mult = float(param_dict['scale_mult'])
		if 'sigma_add' in param_dict:
			sigma_add = float(param_dict['sigma_add'])
		if 'sigma_proj' in param_dict:
			sigma_proj = float(param_dict['sigma_proj'])
		if 'sigma2_proj' in param_dict:
			sigma2_proj = float(param_dict['sigma2_proj'])
		if 'sigma_gauss' in param_dict:
			sigma_gauss = float(param_dict['sigma_gauss'])	
		if 'sigma_mic' in param_dict:
			sigma_mic = float(param_dict['sigma_mic'])
		if 'sigma2_mic' in param_dict:
			sigma2_mic = float(param_dict['sigma2_mic'])
		if 'sigma_gauss_mic' in param_dict:
			sigma_gauss_mic = float(param_dict['sigma_gauss_mic'])	
			
		from filter import filt_gaussl, filt_ctf
		from utilities import drop_spider_doc, even_angles, model_gauss, delete_bdb, model_blank,pad,model_gauss_noise,set_params2D, set_params_proj
		from projection import prep_vol,prgs
		seed(14567)
		delta = 29
		angles = even_angles(delta, 0.0, 89.9, 0.0, 359.9, "S")
		nangle = len(angles)
		
		modelvol = EMData()
		#modelvol.read_image("../model_structure.hdf")
		modelvol.read_image(inpstr)
		
		nx = modelvol.get_xsize()
		
		if nx != boxsize:
			print "requested box dimension does not match dimension of the input model....Exiting"
			sys.exit()

		nvol = 10
		volfts = [None]*nvol
		for i in xrange(nvol):
			sigma = sigma_add + random()  # 1.5-2.5
			addon = model_gauss(sigma, boxsize, boxsize, boxsize, sigma, sigma, 38, 38, 40 )
			scale = scale_mult * (0.5+random())
			model = modelvol + scale*addon
			volfts[i], kb = prep_vol(modelvol + scale*addon)
			
		if parm_format == "bdb":
			stack_data = "bdb:"+outstk
			delete_bdb(stack_data)
		else:
			stack_data = outstk + ".hdf"
		Cs      = 2.0
		pixel   = parm_apix
		voltage = 120.0
		ampcont = 10.0
		ibd     = 4096/2-boxsize
		iprj    = 0

		width = 240
		xstart = 8 + boxsize/2
		ystart = 8 + boxsize/2
		rowlen = 17

		params = []
		for idef in xrange(3, 8):

			irow = 0
			icol = 0

			mic = model_blank(4096, 4096)
			defocus = idef * 0.2
			if parm_CTF:
# 				ctf = EMAN2Ctf()
# 				ctf.from_dict({"defocus": defocus, "cs": Cs, "voltage": voltage, "apix": pixel, "ampcont": ampcont, "bfactor": 0.0})
				astampl=defocus*0.15
				astangl=50.0
				ctf = generate_ctf([defocus, Cs, voltage,  pixel, ampcont, 0.0, astampl, astangl])
# 				print {"defocus":defocus, "astampl":astampl, "astangl":astangl}

			for i in xrange(nangle):
				for k in xrange(12):
					dphi = 8.0*(random()-0.5)
					dtht = 8.0*(random()-0.5)
					psi  = 360.0*random()

					phi = angles[i][0]+dphi
					tht = angles[i][1]+dtht

					s2x = 4.0*(random()-0.5)
					s2y = 4.0*(random()-0.5)

					params.append([phi, tht, psi, s2x, s2y])

					ivol = iprj % nvol
					proj = prgs(volfts[ivol], kb, [phi, tht, psi, -s2x, -s2y])
		
					x = xstart + irow * width
					y = ystart + icol * width

					mic += pad(proj, 4096, 4096, 1, 0.0, x-2048, y-2048, 0)
			
					proj = proj + model_gauss_noise( sigma_proj, nx, nx )
					if parm_CTF:
						proj = filt_ctf(proj, ctf)
						proj.set_attr_dict({"ctf":ctf, "ctf_applied":0})
			
					proj = proj + filt_gaussl(model_gauss_noise(sigma2_proj, nx, nx), sigma_gauss)
					proj.set_attr("active", 1)
					# flags describing the status of the image (1 = true, 0 = false)
					set_params2D(proj, [0.0, 0.0, 0.0, 0, 1.0])
					set_params_proj(proj, [phi, tht, psi, s2x, s2y])

					proj.write_image(stack_data, iprj)
			
					icol += 1
					if icol == rowlen:
						icol = 0
						irow += 1

					iprj += 1

			mic += model_gauss_noise(sigma_mic,4096,4096)
			if parm_CTF:
				#apply CTF
				mic = filt_ctf(mic, ctf)
			mic += filt_gaussl(model_gauss_noise(sigma2_mic, 4096, 4096), sigma_gauss_mic)
	
			mic.write_image(micpref + "%1d.hdf" % (idef-3), 0)
		
		drop_spider_doc("params.txt", params)

	if options.importctf != None:
		print ' IMPORTCTF  '
		from utilities import read_text_row,write_text_row
		from random import randint
		import subprocess
		grpfile = 'groupid%04d'%randint(1000,9999)
		ctfpfile = 'ctfpfile%04d'%randint(1000,9999)
		cterr = [options.defocuserror/100.0, options.astigmatismerror]
		ctfs = read_text_row(options.importctf)
		for kk in xrange(len(ctfs)):
			root,name = os.path.split(ctfs[kk][-1])
			ctfs[kk][-1] = name[:-4]
		if(options.input[:4] != 'bdb:'):
			ERROR('Sorry, only bdb files implemented','importctf',1)
		d = options.input[4:]
		#try:     str = d.index('*')
		#except:  str = -1
		from string import split
		import glob
		uu = os.path.split(d)
		uu = os.path.join(uu[0],'EMAN2DB',uu[1]+'.bdb')
		flist = glob.glob(uu)
		for i in xrange(len(flist)):
			root,name = os.path.split(flist[i])
			root = root[:-7]
			name = name[:-4]
			fil = 'bdb:'+os.path.join(root,name)
			sourcemic = EMUtil.get_all_attributes(fil,'ptcl_source_image')
			nn = len(sourcemic)
			gctfp = []
			groupid = []
			for kk in xrange(nn):
				junk,name2 = os.path.split(sourcemic[kk])
				name2 = name2[:-4]
				ctfp = [-1.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
				for ll in xrange(len(ctfs)):
					if(name2 == ctfs[ll][-1]):
						#  found correct
						if(ctfs[ll][8]/ctfs[ll][0] <= cterr[0]):
							#  acceptable defocus error
							ctfp = ctfs[ll][:8]
							if(ctfs[ll][10] > cterr[1] ):
								# error of astigmatism exceed the threshold, set astigmatism to zero.
								ctfp[6] = 0.0
								ctfp[7] = 0.0
							gctfp.append(ctfp)
							groupid.append(kk)
						break
			if(len(groupid) > 0):
				write_text_row(groupid, grpfile)
				write_text_row(gctfp, ctfpfile)
				cmd = "{} {} {} {}".format('e2bdb.py',fil,'--makevstack=bdb:'+root+'G'+name,'--list='+grpfile)
				#print cmd
				subprocess.call(cmd, shell=True)
				cmd = "{} {} {} {}".format('sxheader.py','bdb:'+root+'G'+name,'--params=ctf','--import='+ctfpfile)
				#print cmd
				subprocess.call(cmd, shell=True)
			else:
				print  ' >>>  Group ',name,'  skipped.'
				
		cmd = "{} {} {}".format("rm -f",grpfile,ctfpfile)
		subprocess.call(cmd, shell=True)
		

if __name__ == "__main__":
	main()
