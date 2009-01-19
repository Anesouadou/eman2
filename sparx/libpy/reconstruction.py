#
# Author: Pawel A.Penczek, 09/09/2006 (Pawel.A.Penczek@uth.tmc.edu)
# Copyright (c) 2000-2006 The University of Texas - Houston Medical School
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#
from EMAN2_cppwrap import *
from global_def import *

def rec2D(  lines, idrange=None, snr=None ):
	"""Perform a 2D reconstruction on a set of 1D lines using nearest neighbouring reverse FFT algorithm.
	   Input: a set of 1D lines
	   Output: a 2D image
	"""

	assert len(lines) > 0


	size = lines[0].get_xsize();

        if snr is None:
	    params = {"size":size, "npad":4, "ndim":2}
        else: 
	    params = {"size":size, "npad":4, "ndim":2, "snr":snr}
        
	r = Reconstructors.get("nn4", params)
	r.setup()

        if idrange is None:
           idrange = xrange( len(lines) )

	t = Transform()
	for i in idrange:
		r.insert_slice( lines[i], t )

	return r.finish()

def recons3d_4nn_ctf(stack_name, list_proj = [], snr = 10.0, sign=1, symmetry="c1", verbose=0, npad=4):
	"""Perform a 3-D reconstruction using Pawel's FFT Back Projection algoritm.
	   
	   Input:
	    stack_name - name of the stack file on a disk,
	                 each image has to have the following attributes set:
			 psi, theta, phi, sx, sy, defocus, 
	    list_proj - list of images from stack_name to be included in the reconstruction
	    symmetry	 -- Point group of the target molecule (defaults to "C1")

	   Return:  3d reconstructed volume image

	   Usage:
	     
	     anglelist = getAngles("myangles.txt") # not yet written
	     vol = do_reconstruction(filepattern, start, end, anglelist, symmetry)
	"""
	import types
	# read first image to determine the size to use
	if list_proj == []:	
		if type(stack_name) == types.StringType: nima = EMUtil.get_image_count(stack_name)
		else : nima = len(stack_name)
		list_proj = xrange(nima) 
	# read first image to determine the size to use
	if type(stack_name) == types.StringType:
		proj = EMData()
		proj.read_image(stack_name, list_proj[0])
	else:    proj = stack_name[list_proj[0]].copy()
	
	# convert angles to transform (rotation) objects
	active = proj.get_attr_default('active', 1)
	size   = proj.get_xsize()

	padffted = proj.get_attr_default("padffed", 0)

	if padffted == 1 :
		size = size /npad

	elif size != proj.get_ysize():
		ERROR("input data has to be square","recons3d_4nn_ctf",1)

	# reconstructor
	params = {"size":size, "npad":npad, "symmetry":symmetry, "snr":snr, "sign":sign}
	r = Reconstructors.get("nn4_ctf", params)
	r.setup()


	if type(stack_name) == types.StringType:
		for i in xrange(len(list_proj)):
			proj.read_image(stack_name, list_proj[i])
			active = proj.get_attr_default('active', 1)
			if(active == 1):
				xform_proj = proj.get_attr( "xform.projection" )
				r.insert_slice(proj, xform_proj )
	else:
		for i in xrange(len(list_proj)):
			active = stack_name[list_proj[i]].get_attr_default('active', 1)
			if(active == 1):
				xform_proj = stack_name[list_proj[i]].get_attr( "xform.projection" )
				r.insert_slice(stack_name[list_proj[i]], xform_proj )
	return r.finish()

def recons3d_4nn_ctf_MPI(myid, prjlist, snr, sign=1, symmetry="c1", info=None):
	from utilities import reduce_EMData_to_root
	if( len(prjlist) == 0 ):
	    ERROR("empty input list","recons3d_4nn_ctf_MPI",1)

	imgsize = prjlist[0].get_xsize()
	if prjlist[0].get_ysize() != imgsize:
		ERROR("input data has to be square","recons3d_4nn_ctf_MPI",1)


	fftvol = EMData()
	weight = EMData()

	params = {"size":imgsize, "npad":4, "snr":snr, "sign":sign, "symmetry":symmetry, "fftvol":fftvol, "weight":weight}
	r = Reconstructors.get( "nn4_ctf", params )
	r.setup()

	if( not (info is None) ): nimg = 0
	for prj in prjlist :
		if prj.get_xsize() != imgsize or prj.get_ysize() != imgsize:
			ERROR("inconsistent image size","recons3d_4nn_ctf_MPI",1)

		active = prj.get_attr_default('active', 1)
		if(active == 1):
			xform_proj = prj.get_attr( "xform.projection" )
			r.insert_slice(prj, xform_proj )
		if( not (info is None) ):
			nimg += 1
			info.write(" %4d inserted\n" %(nimg) )
			info.flush()
	#  WEI:  what to do is no particles were active, thus none was inserted PAP  10/30/08
	if( not (info is None) ): 
		info.write( "begin reduce\n" )
		info.flush()

	reduce_EMData_to_root(fftvol, myid)
	reduce_EMData_to_root(weight, myid)

	if( not (info is None) ): 
		info.write( "after reduce\n" )
		info.flush()

	if myid == 0 : vol = r.finish()
	else:           vol = None

	return vol

def recons3d_4nn(stack_name, list_proj=[], symmetry="c1", npad=4, snr=None):
	"""
	Perform a 3-D reconstruction using Pawel's FFT Back Projection algoritm.
	   
	Input:
	   stack_name - name of the file with projection data.
	   
	   list_proj - 

	   symmetry - Point group of the target molecule (defaults to "C1")
	   
	   npad - 

	   Angles and shifts are passed in the file header as set_attr. Keywords are phi, theta, psi, sx, sy

	   Return:  3D reconstructed volume image

	   Usage:
	     vol = recons3d_4nn(filepattern, list_proj, symmetry)
	"""
	import types
	if list_proj == []:
		if type(stack_name) == types.StringType: nima = EMUtil.get_image_count(stack_name)
		else : nima = len(stack_name)
		list_proj = xrange(nima) 
	# read first image to determine the size to use
	if type(stack_name) == types.StringType:
		proj = EMData()
		proj.read_image(stack_name, list_proj[0])
	else:    proj = stack_name[list_proj[0]].copy()

	size = proj.get_xsize()
	# sanity check -- image must be square
	if size != proj.get_ysize():
		ERROR("input data has to be square","recons3d_4nn",1)
	# reconstructor
	if snr is None:
		params = {"size":size, "npad":npad, "symmetry":symmetry}
	else:
		params = {"size":size, "npad":npad, "symmetry":symmetry, "snr":snr}
	
	r = Reconstructors.get("nn4", params)
	r.setup()
	
	if type(stack_name) == types.StringType:
		for i in xrange(len(list_proj)):
			proj.read_image(stack_name, list_proj[i])
			active = proj.get_attr_default('active', 1)
			if(active == 1):
				xform_proj = proj.get_attr( "xform.projection" )
				r.insert_slice(proj, xform_proj )
	else:
		for i in list_proj:
			active = stack_name[i].get_attr_default('active', 1)
			if(active == 1):
				xform_proj = stack_name[i].get_attr( "xform.projection" )
				r.insert_slice(stack_name[i], xform_proj )
	return r.finish()

def recons3d_4nn_MPI(myid, prjlist, symmetry="c1", info=None):
	from utilities import reduce_EMData_to_root
	if( len(prjlist) == 0 ):
	    ERROR("empty input list","recons3d_4nn_ctf_MPI",1)

	imgsize = prjlist[0].get_xsize()
	if prjlist[0].get_ysize() != imgsize:
		ERROR("input data has to be square","recons3d_4nn_ctf_MPI",1)

	fftvol = EMData()
	weight = EMData()

	params = {"size":imgsize, "npad":4, "symmetry":symmetry, "fftvol":fftvol, "weight":weight}
	r = Reconstructors.get( "nn4", params )
	r.setup()
	if( not (info is None) ): nimg = 0
	for prj in prjlist :
		if prj.get_xsize() != imgsize or prj.get_ysize() != imgsize:
			ERROR("inconsistent image size","recons3d_4nn_ctf_MPI",1)

		active = prj.get_attr_default('active', 1)
		if(active == 1):
			xform_proj = prj.get_attr( "xform.projection" )
			r.insert_slice(prj, xform_proj )
		if( not (info is None) ):
			nimg += 1
			info.write(" %4d inserted\n" %(nimg) )
			info.flush()
	#  Wei, what if none are active?
	if( not (info is None) ): 
		info.write( "begin reduce\n" )
		info.flush()

	reduce_EMData_to_root(fftvol, myid)
	reduce_EMData_to_root(weight, myid)

	if( not (info is None) ): 
		info.write( "after reduce\n" )
		info.flush()

	if myid == 0 :  vol = r.finish()
	else:           vol = None
	return vol

def recons3d_nn_SSNR(stack_name,  mask2D = None, ring_width=1, npad =1, sign=1, symmetry="c1", CTF = False, random_angles = 0):
	
	"""
	Perform a 3-D reconstruction using nearest neighbor interpolation and 
	calculate 3D spectral signal-to-noise ratio (SSNR)	   
	Input : stack_name - Name of the file with projection data.
		CTF        - 
	        symmetry   - Point group of the target molecule (default "c1")
		npad       - Times of padding applied, default is 1
		sign       - Currently not used, may be used in the future
		w          - The thickness of the shell, default is 1
		filename   - The filename in which you can save the SSNR results 
	Return: reconstructed 3D SSNR volume
        Usage : vol = recons3d_nn_SSNR(stack_name, CTF, symmetry, npad, snr, sign, w, filename])
	CTF true:
	variance at one voxel  = Gamma^2d->3d [ |F_k^2D|^2   +  ctf^2*|P^2D->3D(F^3D)|^2 -
	          -2*Real(conj(F_k^2D)*ctf*P^2D->3D(F^3D))]	
	signal  at one voxel   = Gamma^2d->3d [ |F_k^2D|^2  ]
	SSNR =  sum_rot [ wght*signal/Kn ]/sum_rot[ wght*variance /(Kn(Kn-1))] -1
	Notice: wght is always turned on during SSNR calculation.
	"""
	import types
	# Yang add a safety on 05/22/07
	if type(stack_name) == types.StringType: nima = EMUtil.get_image_count(stack_name)
	else :                                   nima = len(stack_name)
	# read first image to determine the size to use
	if type(stack_name) == types.StringType:
		proj = EMData()	
		proj.read_image(stack_name, 0)
	else:    
		proj = stack_name[0].copy()
	#active = proj.get_attr('active')
	size   = proj.get_xsize()	
	# sanity check -- image must be square
	if size != proj.get_ysize(): ERROR("input data has to be square","recons3d_nn_SSNR",1)
	# reconstructor
	SSNR = EMData()
	if CTF :
		params = {"size":size, "npad":npad, "symmetry":symmetry, "SSNR":SSNR, "w":ring_width, "sign":sign}
		r = Reconstructors.get("nnSSNR_ctf", params)
	else :
		params = {"size":size, "npad":npad, "symmetry":symmetry, "SSNR":SSNR, "w":ring_width}
		r = Reconstructors.get("nnSSNR", params)
	r.setup()

	for i in xrange(nima):
		if type(stack_name) == types.StringType:
			proj.read_image(stack_name, i)
		else:
			proj = stack_name[i]
		active = proj.get_attr_default('active', 1)
		if(active == 1):
			if(random_angles  == 2):
				from  random import  random
				phi    = 360.0*random()
				theta  = 180.0*random()
				psi    = 360.0*random()
				xform_proj = Transform( {"type":"spider", "phi":phi, "theta":theta, "psi":psi} )
			elif(random_angles  == 3):
				from  random import  random
				phi    = 360.0*random()
				theta  = 180.0*random()
				psi    = 360.0*random()
				tx     = 6.0*(random() - 0.5)
				ty     = 6.0*(random() - 0.5)
				xform_proj = Transform( {"type":"spider", "phi":phi, "theta":theta, "psi":psi, "tx":tx, "ty":ty} )
			elif(random_angles  == 1):
				from  random import  random
				old_xform_proj = proj.get_attr( "xform.projection" )
				dict = old_xform_proj.get_rotation( "spider" )
				dict["psi"] = 360.0*random()
				xform_proj = Transform( dict )
			else:
				xform_proj = proj.get_attr( "xform.projection" )

		 	if mask2D:
				stats = Util.infomask(proj, mask2D, True)
				proj -= stats[0]
				proj *= mask2D
			r.insert_slice(proj, xform_proj)
	vol_ssnr = r.finish()
	outlist = [[] for i in xrange(6)]
	nn = SSNR.get_xsize()
	for i in xrange(1,nn): outlist[0].append((float(i)-0.5)/(float(nn-1)*2))
	for i in xrange(1,nn):
		if(SSNR(i,1,0) > 0.0):
			outlist[1].append(max(0.0,(SSNR(i,0,0)/SSNR(i,1,0)-1.)))      # SSNR
		else:
			outlist[1].append(0.0)
	for i in xrange(1,nn): outlist[2].append(SSNR(i,1,0)/SSNR(i,2,0))	          # variance
	for i in xrange(1,nn): outlist[3].append(SSNR(i,2,0))				  # number of points in the shell
	for i in xrange(1,nn): outlist[4].append(SSNR(i,3,0))				  # number of added Fourier points
	for i in xrange(1,nn): outlist[5].append(SSNR(i,0,0))				  # square of signal
	return [outlist, vol_ssnr]

def recons3d_nn_SSNR_MPI(myid, prjlist, mask2D, ring_width=1, npad =1, sign=1, symmetry="c1", CTF = False, random_angles = 0):
	from utilities import reduce_EMData_
	to_root,bcast_EMData_to_all, bcast_number_to_all
	if( len(prjlist) == 0 ):    ERROR("empty input list","recons3d_nn_SSNR_MPI",1)
	imgsize = prjlist[0].get_xsize()
	if prjlist[0].get_ysize() != imgsize:  ERROR("input data has to be square","recons3d_nn_SSNR_MPI",1)
	fftvol   = EMData()
	weight   = EMData()
	weight2  = EMData()
	SSNR     = EMData()
	if CTF:
		weight3  = EMData()
		params = { "size":imgsize, "npad":npad, "sign":sign, "symmetry":symmetry, "SSNR":SSNR,\
		           "fftvol":fftvol, "weight":weight, "weight2":weight2, "weight3":weight3, "w":ring_width }
		r = Reconstructors.get( "nnSSNR_ctf", params )
	else   :
		params = {"size":imgsize, "npad":npad, "symmetry":symmetry, "SSNR":SSNR,"fftvol":fftvol, "weight":weight, "weight2":weight2, "w":ring_width }
		r = Reconstructors.get( "nnSSNR",     params )
	r.setup()

	if prjlist[0].get_xsize() != imgsize or prjlist[0].get_ysize() != imgsize: ERROR("inconsistent image size","recons3d_nn_SSNR_MPI",1)
	for prj in prjlist:
		active = prj.get_attr_default('active', 1)
		if(active == 1):
			if(random_angles  == 2):
				from  random import  random
				phi	 = 360.0*random()
				theta    = 180.0*random()
				psi	 = 360.0*random()
				xform_proj = Transform( {"type":"spider", "phi":phi, "theta":theta, "psi":psi} )
			elif(random_angles  == 3):
				from  random import  random
				phi    = 360.0*random()
				theta  = 180.0*random()
				psi    = 360.0*random()
				tx     = 6.0*(random() - 0.5)
				ty     = 6.0*(random() - 0.5)
				xform_proj = Transform( {"type":"spider", "phi":phi, "theta":theta, "psi":psi, "tx":tx, "ty":ty} )
			elif(random_angles  == 1):
				from  random import  random
				old_xform_proj = prj.get_attr( "xform.projection" )
				dict = old_xform_proj.get_rotation( "spider" )
				dict["psi"] = 360.0*random()
				xform_proj = Transform( dict )
			else:
				xform_proj = prj.get_attr( "xform.projection" )
			if mask2D:
				stats = Util.infomask(prj, mask2D, True)
				prj -= stats[0]
				prj *= mask2D
			r.insert_slice(prj, xform_proj )
	#  WEI: what if none inserted
	#from utilities import info
	reduce_EMData_to_root(weight,  myid, 0)
	reduce_EMData_to_root(fftvol,  myid, 0)
	reduce_EMData_to_root(weight2, myid, 0)
	if CTF: reduce_EMData_to_root(weight3, myid, 0)
	if myid == 0 :
		vol_ssnr = r.finish()
		outlist = [[] for i in xrange(6)]
		nn = SSNR.get_xsize()
		for i in xrange(1,nn): outlist[0].append((float(i)-0.5)/(float(nn-1)*2))
		for i in xrange(1,nn):
			if(SSNR(i,1,0) > 0.0):
				outlist[1].append(max(0.0,(SSNR(i,0,0)/SSNR(i,1,0)-1.)))     # SSNR
			else:
				outlist[1].append(0.0)
		for i in xrange(1,nn): outlist[2].append(SSNR(i,1,0)/SSNR(i,2,0))	         # variance
		for i in xrange(1,nn): outlist[3].append(SSNR(i,2,0))				  # number of points in the shell
		for i in xrange(1,nn): outlist[4].append(SSNR(i,3,0))				  # number of added Fourier points
		for i in xrange(1,nn): outlist[5].append(SSNR(i,0,0))				  # square of signal
		return [outlist, vol_ssnr]

class memory_store:
    def __init__(self, npad):
        self.m_npad = npad
        self.m_imgs = []

    def add_image(self, img):
        self.m_imgs.append(img)
    
    def get_image(self, id):
        return self.m_imgs[id]
          
def bootstrap_nn(proj_stack, volume_stack, list_proj, niter, media="memory", npad=4, symmetry="c1", output=-1, CTF=False, snr=1.0, sign=1, myseed=None ):
	from random import seed
	from random import randint
	from time   import time
	from sys    import stdout
	from utilities import set_ctf
	if(output == -1):
		import sys
		output=sys.stdout

	if not(myseed is None):
		seed(myseed) 

	nimages = len(list_proj)
	if nimages == 0 :
		print "empty list of projections input!"
		return None


	if media=="memory" :
		store = memory_store(npad)
	else :
		store = file_store(media,npad, 0, CTF)
		if not(output is None):
			output.flush()

	proj = EMData()
	proj.read_image(proj_stack,list_proj[0])
	
	size = proj.get_xsize()
	if size != proj.get_ysize():
		print "Image projections must be square!"
		return None
	
	#for j in xrange(nimages):
	#    proj = EMData()
	#    proj.read_image(proj_stack, j)
        #store.add_image( proj )

        #if (j+1) % 1000  == 0 :
        #    output.write( "%d image read\n" % (j+1) )
        #    output.flush()

        overall_start = time()
	for i in xrange(niter):
		iter_start = time()
        	mults = nimages*[0]
		for j in xrange(nimages):
        		imgid = randint(0,nimages-1)
        		mults[imgid]=mults[imgid]+1

		if CTF:
        		params = {"size":size, "npad":npad, "symmetry":symmetry, "snr":snr, "sign":sign}
        		r = Reconstructors.get("nn4_ctf", params);
		else:
			params = {"size":size, "npad":npad, "symmetry":symmetry, "snr":snr}
			r = Reconstructors.get("nn4", params);
        	

        	r.setup()
        	if not(output is None):
			output.write( "Bootstrap volume %8d " % i )
			output.flush()

        	store.restart()

        	if not(output is None):
			output.write( "Inserting images " )
        		output.flush()

        	for j in xrange(nimages):
			if mults[j] > 0 :
        			img_j = EMData()
        			store.get_image( j, img_j );
		    		img_j.set_attr( "mult", mults[j] );
				phi_j = img_j.get_attr( "phi" )
				tht_j = img_j.get_attr( "theta" )
				psi_j = img_j.get_attr( "psi" )
				tra_j = Transform( {"type":"spider", "phi":phi_j, "theta":tht_j, "psi":psi_j} )

				if CTF:
					cs = img_j.get_attr( "Cs" )
					pixel   = img_j.get_attr( "Pixel_size" )
					defocus = img_j.get_attr( "defocus" )
					voltage = img_j.get_attr( "voltage" )
					ampcont = img_j.get_attr( "amp_contrast" )
					bfactor = 0.0
					set_ctf( img_j, [defocus, cs, voltage, pixel, bfactor, ampcont] )
        		
		    		r.insert_slice(img_j, tra_j)

        			#[mean,sigma,min,max]= Util.infomask(img_j, None, False)
        			#output.write( "img %4d %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f\n" % (j, mean, sigma, min, max, phi, theta, psi) )
        			#output.flush()

		if not(output is None):
			output.write( "Finishing... " )
			output.flush( )

		vol = r.finish()

		if not(output is None):
			output.write( "Writing... " )
			output.flush()

		vol.write_image(volume_stack,i)

        	if not(output is None):
			output.write( " done!" )
			output.write( " time %15.3f %15.3f \n" % (time()-iter_start,time()-overall_start) )
        		output.flush()

def recons3d_sirt(stack_name, list_proj, radius, lam=1.0e-4, maxit=100, symmetry="c1", tol=0.001):
	#
	# tol	-- convergence tolerance
	# lam	-- damping parameter
	# maxit -- maximum number of iterations
	#
	from math import sqrt
	from utilities import model_circle
	#  analyze the symmetries Phil's code has all symmetries ready...
	nsym=1

	#  get image size from the first image
	data = EMData()
	data.read_image(stack_name,list_proj[0])
	nx = data.get_xsize()
	mask2d=model_circle(radius,nx,nx)  # SIRT works for squares only!
	mask2d = 1.0 - mask2d  # invert the mask to get average in corners
	nangles = len(list_proj)
	#
	mask3d=model_circle(radius,nx,nx,nx) # a 3D mask for error calculation
	#
	# create a volume to hold the reconstruction 
	#
	xvol = EMData()
	xvol.set_size(nx,nx,nx)
	xvol.to_zero()
	#
	# create a volume to hold trans(P)*P*xvol
	#
	pxvol = xvol.copy()
	#  array of symmetrized angles
	symangles=3*[0.0]
	angles = []

	# start iterating
	iter  = 1
	old_rnorm = 1.0
	while iter <= maxit:
		if (iter == 1):
			#
			# backproject 2D images first to create the right-hand side of the
			# the normal equation
			#
			bvol = EMData()
			bvol.set_size(nx,nx,nx)
			bvol.to_zero()
			for i in xrange(nangles):
				# read projections and do initial backprojection
				data.read_image(stack_name,list_proj[i])
				stat=Util.infomask(data,mask2d,False)
				data=data-stat[0]   # subtract the background average in the corners
				
				RA = data.get_attr( "xform.projection" )

				angles.append(RA)
				#ATTENTION
				#for transform in Symmetry3D.get_symmetries(symmetry):
					#Tf = transform*RA
					# though why do you go from 1 to nysm? why not 0 to nysm-1 ? It should be
					# equivalent unless I am missing something
					#angdict = Tf.get_params("spider")
					# then continue as before
				for ns in xrange(1,nsym+1):
					# multiply myangles by symmetry using Phil's Transform class
					Tf=RA.get_sym(symmetry,ns) #
					angdict = Tf.get_rotation("spider")
					#				    Chao - please check the order of phi, theta, psi
					symangles[0] = angdict["phi"]
					symangles[1] = angdict["theta"]
					symangles[2] = angdict["psi"]
					myparams = {"angletype":"SPIDER",
					     	    "anglelist":symangles,
					     	    "radius":radius}
					bvol += data.backproject("chao",myparams)
			bnorm = sqrt(bvol.cmp("dot",bvol,{"mask":mask3d,"negative":0}))
			grad  = bvol
		else:
			#  Insert your favorite MPI here
			pxvol.to_zero() 
			for i in xrange(nangles):
				# just a single slice of phi, theta, psi
				RA = angles[i]
				for ns in xrange(1,nsym+1):
					# multiply myangles by symmetry using Phil's Transform class
					Tf = RA.get_sym(symmetry,ns)#Tf.get_rotation()
					angdict = Tf.get_rotation("spider")
					#				    Chao - please check the order of phi, theta, psi
					symangles[0] = angdict["phi"]
					symangles[1] = angdict["theta"]
					symangles[2] = angdict["psi"]
					myparams = {"angletype":"SPIDER",
					    	    "anglelist":symangles,
					    	    "radius":radius}
					data  = xvol.project("chao", myparams) 
					pxvol += data.backproject("chao",myparams)
			grad  = bvol - pxvol

		rnorm = sqrt(grad.cmp("dot",grad,{"mask":mask3d,"negative":0}))
		print 'iter = %3d,  rnorm = %6.3f' % (iter,rnorm/bnorm)
		if (rnorm < tol or rnorm > old_rnorm): break
		old_rnorm = rnorm
		xvol = xvol + lam*grad
		iter = iter + 1

	return  xvol
      

def recons3d_wbp(stack_name, list_proj, method, const=1.0E4, symmetry="c1"):  
	import types
	if type(stack_name) == types.StringType:
		B = EMData()
		B.read_image(stack_name,list_proj[0])
	else : B = stack_name[list_proj[0]].copy()
	   
	nsam = B.get_xsize()
	nrow = B.get_ysize()
	nsli = B.get_zsize()

	nx3d = nrow
	ny3d = nrow
	nz3d = nrow

	CUBE = EMData()
	CUBE.set_size(nx3d, ny3d, nz3d)
	CUBE.to_zero()

	RA = Transform()
	nsym = RA.get_nsym(symmetry)

	nimages = len(list_proj)
	ntripletsWnsym = nsym*nimages
	dm=[0.0]*(9*ntripletsWnsym)
	ss=[0.0]*(6*ntripletsWnsym)
	count = 0
	"""
	for i in xrange(nimages):
		if type(stack_name) == types.StringType:
			B.read_image(stack_name,list_proj[i], True)
			RA = B.get_attr( "xform.projection" )
		else:  
			RA = stack_name[list_proj[i]].get_attr( "xform.projection" )
		for j in xrange(nsym):
			Tf = RA.get_sym(symmetry,j) #Tf.get_rotation()
			angdict = Tf.get_rotation("spider")
			PHI   = angdict["phi"]
			THETA = angdict["theta"]
			PSI   = angdict["psi"]
			DMnSS = Util.CANG(PHI,THETA,PSI)
			dm[(count*9) :(count+1)*9] = DMnSS["DM"]
			ss[(count*6) :(count+1)*6] = DMnSS["SS"]
			count += 1
	"""
	from utilities import get_params_proj
	for i in xrange(nimages):
		if type(stack_name) == types.StringType:
			B.read_image(stack_name,list_proj[i], True)
			PHI, THETA, PSI, s2x, s2y = get_params_proj( B )
		else:  
			PHI, THETA, PSI, s2x, s2y = get_params_proj( stack_name[list_proj[i]] )
		DMnSS = Util.CANG(PHI,THETA,PSI)
		dm[(count*9) :(count+1)*9] = DMnSS["DM"]
		ss[(count*6) :(count+1)*6] = DMnSS["SS"]
		count += 1

	if(method=="general"):
	# for general weighting tabularize table of exponents
		expdict =  Util.ExpMinus4YSqr(2.0, 1000)
		exptable = expdict["table"]

	count = 1
	for i in xrange(nimages):
		if type(stack_name) == types.StringType: B.read_image(stack_name,list_proj[i])
		else : B = stack_name[list_proj[i]].copy()
		for j in xrange(nsym):
			DM = dm[((j*nsym+list_proj[i])*9) :(j*nsym+list_proj[i]+1)*9]
			if   (method=="general"):    Util.WTF(B, ss, const, count, exptable)
			elif (method=="exact"  ):    Util.WTM(B, ss, const, count)
			Util.BPCQ(B,CUBE,DM)
			count += 1

	return CUBE

def prepare_recons(data, symmetry, myid, main_node_half, half_start, step, index, info=None):
	from random import randint
	from utilities import reduce_EMData_to_root
	from mpi import mpi_barrier, MPI_COMM_WORLD
	nx = data[0].get_xsize()

	fftvol_half = EMData()
	weight_half = EMData()
	half_params = {"size":nx, "npad":4, "symmetry":symmetry, "fftvol":fftvol_half, "weight":weight_half}
	half = Reconstructors.get( "nn4", half_params )
	half.setup()

	group = -1
	for i in xrange(half_start, len(data), step):
		if(index >-1 ):  group = data[i].get_attr('group')
		if(group == index):
			if( data[i].get_attr_default('active',1) == 1):
				xform_proj = data[i].get_attr( "xform.projection" )
				if not(info is None):
					info.write( "inserting half %d\n" % i )
					info.flush()
				half.insert_slice(data[i], xform_proj )

	if not(info is None):
		info.write( "begin reduce half\n" )
		info.flush()

	reduce_EMData_to_root(fftvol_half, myid, main_node_half)
	reduce_EMData_to_root(weight_half, myid, main_node_half)

	if not(info is None):
		info.write( "after reduce half\n" )
		info.flush()

	if myid == main_node_half:
		tmpid = randint(0, 1000000)
		fftvol_half_file = ("/tmp/fftvol_half%d.hdf" % tmpid)
		weight_half_file = ("/tmp/weight_half%d.hdf" % tmpid)
		fftvol_half.write_image(fftvol_half_file)
		weight_half.write_image(weight_half_file)
	mpi_barrier(MPI_COMM_WORLD)

	fftvol_half = None
	weight_half = None

	if myid == main_node_half:  return fftvol_half_file,weight_half_file

	return None,None


def prepare_recons_ctf_fftvol(data, snr, symmetry, myid, main_node_half, pidlist, info=None):
	from random import randint
	from utilities import reduce_EMData_to_root
	nx = data[0].get_xsize()
        
	fftvol_half = EMData()
	weight_half = EMData()
	half_params = {"size":nx, "npad":4, "snr":snr, "sign":1, "symmetry":symmetry, "fftvol":fftvol_half, "weight":weight_half}
	half = Reconstructors.get( "nn4_ctf", half_params )
	half.setup()
        
	for i in pidlist:
		if( data[i].get_attr_default('active', 1) == 1):
			xform_proj = data[i].get_attr( "xform.projection" )
                	if not(info is None):
				info.write( "inserting half %d\n" % i )
                		info.flush()
			half.insert_slice(data[i], xform_proj )
        
	if not(info is None):
		info.write( "begin reduce half\n" )
		info.flush()

	reduce_EMData_to_root(fftvol_half, myid, main_node_half)
	reduce_EMData_to_root(weight_half, myid, main_node_half)
        
	return fftvol_half, weight_half

def prepare_recons_ctf(nx, data, snr, symmetry, myid, main_node_half, half_start, step, info=None):
	from random import randint
	from utilities import reduce_EMData_to_root
	from mpi import mpi_barrier, MPI_COMM_WORLD

        
	fftvol_half = EMData()
	weight_half = EMData()
	half_params = {"size":nx, "npad":4, "snr":snr, "sign":1, "symmetry":symmetry, "fftvol":fftvol_half, "weight":weight_half}
	half = Reconstructors.get( "nn4_ctf", half_params )
	half.setup()
        
	for i in xrange(half_start, len(data), step):
		if( data[i].get_attr_default('active',1) == 1):
			xform_proj = data[i].get_attr( "xform.projection" )
			if not(info is None):
				info.write( "inserting half %d\n" % i )
                		info.flush()
			half.insert_slice(data[i], xform_proj )
        
	if not(info is None):
        	info.write( "begin reduce half\n" )
        	info.flush()

	reduce_EMData_to_root(fftvol_half, myid, main_node_half)
	reduce_EMData_to_root(weight_half, myid, main_node_half)

	if not(info is None):
		info.write( "after reduce half\n" )
		info.flush()
        
	if myid == main_node_half:
		tmpid = randint(0, 1000000) 
		fftvol_half_file = ("/tmp/fftvol_half%d.hdf" % tmpid)
		weight_half_file = ("/tmp/weight_half%d.hdf" % tmpid)
		fftvol_half.write_image(fftvol_half_file)
		weight_half.write_image(weight_half_file)
	mpi_barrier(MPI_COMM_WORLD)
        
	fftvol_half = None
	weight_half = None

	if myid == main_node_half:
		return fftvol_half_file, weight_half_file

	return None,None

def recons_from_fftvol(size, fftvol, weight, symmetry):
	params = {"size":size, "npad":4, "symmetry":symmetry, "fftvol":fftvol, "weight":weight}
	r = Reconstructors.get("nn4", params)
	r.setup()
	return r.finish()


def recons_ctf_from_fftvol(size, fftvol, weight, snr, symmetry, weighting=1):
	params = {"size":size, "npad":4, "snr":snr, "sign":1, "symmetry":symmetry, "fftvol":fftvol, "weight":weight, "weighting":weighting}
	r = Reconstructors.get("nn4_ctf", params)
	r.setup()
	return r.finish()


def get_image_size( imgdata, myid ):
	from mpi import mpi_gather, mpi_bcast, MPI_COMM_WORLD, MPI_INT
	nimg = len(imgdata)

        nimgs = mpi_gather( nimg, 1, MPI_INT, 1, MPI_INT, 0, MPI_COMM_WORLD )

        if myid==0:
		src = -1
		for i in xrange( len(nimgs) ):
			if int(nimgs[i]) > 0 :
				src = i
				break
		if src==-1:
			return 0
	else:
		src = -1

	size_src = mpi_bcast( src, 1, MPI_INT, 0, MPI_COMM_WORLD )

	if myid==int(size_src[0]):
		assert nimg > 0
		size = imgdata[0].get_xsize()
	else:
		size = -1

	nx = mpi_bcast( size, 1, MPI_INT, size_src[0], MPI_COMM_WORLD )
	return int(nx[0])


def rec3D_MPI(data, snr, symmetry, mask3D, fsc_curve, myid, main_node = 0, rstep = 1.0, odd_start=0, eve_start=1, info=None, index=-1):
	'''
	  This function is to be called within an MPI program to do a reconstruction on a dataset kept 
          in the memory, Computes reconstruction and through odd-even, in order to get the resolution
	'''
	import os
	from statistics import fsc_mask
	from utilities  import model_blank, reduce_EMData_to_root, get_image, send_EMData, recv_EMData
	from random     import randint
	from mpi        import mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	nproc = mpi_comm_size(MPI_COMM_WORLD)

	if nproc==1:
		assert main_node==0
		main_node_odd = main_node
		main_node_eve = main_node
		main_node_all = main_node
	elif nproc==2:
		main_node_odd = main_node
		main_node_eve = (main_node+1)%2
		main_node_all = main_node

		tag_voleve = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002
	else:
		main_node_odd = main_node
		main_node_eve = (int(main_node)+1)%int(nproc)
		main_node_all = (int(main_node)+2)%int(nproc)

		tag_voleve = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002

		tag_fftvol_odd = 1003
		tag_weight_odd = 1004
		tag_volall = 1005


        if index !=-1 :
		grpdata = []
		for i in xrange( len(data) ):
		    if data[i].get_attr( 'group' ) == index:
		    	    grpdata.append( data[i] )
        	imgdata = grpdata
        else:
		imgdata = data

	nx = get_image_size( imgdata, myid )
	if nx==0:
		print "Warning: no images were given for reconstruction, this usually means there is an empty group, returning empty volume"
		return model_blank( 100, 100, 100 ), None

	fftvol_odd_file,weight_odd_file = prepare_recons_ctf(nx, imgdata, snr, symmetry, myid, main_node_odd, odd_start, 2, info)
	fftvol_eve_file,weight_eve_file = prepare_recons_ctf(nx, imgdata, snr, symmetry, myid, main_node_eve, eve_start, 2, info) 

	if nproc == 1:
		fftvol = get_image(fftvol_odd_file)
		weight = get_image(weight_odd_file)
		volodd = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)

		fftvol = get_image(fftvol_eve_file)
		weight = get_image(weight_eve_file)
		voleve = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
                
		fscdat = fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)

		fftvol = get_image( fftvol_odd_file )
		fftvol_tmp = get_image(fftvol_eve_file)
		fftvol += fftvol_tmp
		fftvol_tmp = None

		weight = get_image( weight_odd_file )
		weight_tmp = get_image(weight_eve_file)
		weight += weight_tmp
		weight_tmp = None

		volall = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
		os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file );
		os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file );
 
		return volall,fscdat
  
	if nproc == 2:
		if myid == main_node_odd:
			fftvol = get_image( fftvol_odd_file )
			weight = get_image( weight_odd_file )
			volodd = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
			voleve = recv_EMData(main_node_eve, tag_voleve)
			fscdat = fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)
		else:
			assert myid == main_node_eve
			fftvol = get_image( fftvol_eve_file )
			weight = get_image( weight_eve_file )
			voleve = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
			send_EMData(voleve, main_node_odd, tag_voleve)

		if myid == main_node_odd:
			fftvol = get_image( fftvol_odd_file )
			fftvol_tmp = recv_EMData( main_node_eve, tag_fftvol_eve )
			fftvol += fftvol_tmp
			fftvol_tmp = None

			weight = get_image( weight_odd_file )
			weight_tmp = recv_EMData( main_node_eve, tag_weight_eve )
			weight += weight_tmp
			weight_tmp = None
        	
			volall = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
			os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file )
 
			return volall,fscdat
		else:
			assert myid == main_node_eve
			fftvol = get_image( fftvol_eve_file )
			weight = get_image( weight_eve_file )
			send_EMData(fftvol, main_node_odd, tag_fftvol_eve )
			send_EMData(weight, main_node_odd, tag_weight_eve )
			os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file )
			return model_blank(nx,nx,nx), None
        
	# cases from all other number of processors situations
	if myid == main_node_odd:
		fftvol = get_image(fftvol_odd_file)
		send_EMData(fftvol, main_node_all, tag_fftvol_odd)
                
		if not(info is None):
			info.write( "sent fftvol odd\n" )
			info.flush()

		weight = get_image(weight_odd_file)
                
		if not(info is None):
			info.write( "loaded weight odd\n" )
			info.flush()

		send_EMData(weight, main_node_all, tag_weight_odd)
                
		if not(info is None):
			info.write( "sent weight odd\n" )
			info.write( 'begin recons odd\n' )
			info.flush()

		volodd = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
		if not(info is None):
			info.write( 'recons odd done\n' )
			info.flush()

		voleve = recv_EMData(main_node_eve, tag_voleve)
		if not(info is None):
			info.write( "recv eve done\n" )
			info.flush()

		#from utilities import drop_image
		#drop_image(volodd,"vol1.spi","s")
		#drop_image(voleve,"vol2.spi","s")
		fscdat = fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)
		if not(info is None):
			info.write( "fsc done\n" )
			info.flush()

		volall = recv_EMData(main_node_all, tag_volall)
		if not(info is None):
			info.write( "recv all done\n" )
			info.flush() 

		os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file );
		return volall,fscdat
                 
	if myid == main_node_eve:

		fftvol = get_image( fftvol_eve_file )
		send_EMData(fftvol, main_node_all, tag_fftvol_eve )

		weight = get_image( weight_eve_file )
		send_EMData(weight, main_node_all, tag_weight_eve )

		if not(info is None):
			info.write( 'begin recons eve\n' )
			info.flush()

		voleve = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
		if not(info is None):
			info.write( "recons eve done\n" )
			info.flush()

		send_EMData(voleve, main_node_odd, tag_voleve)
		if not(info is None):
			info.write( "send eve done\n" )
			info.flush()
		os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file )

		return model_blank(nx,nx,nx),None

	if myid == main_node_all:
		fftvol = recv_EMData(main_node_odd, tag_fftvol_odd)
		if not(info is None):
			info.write( "after recv fftvol odd\n" )
			info.flush()

		fftvol_tmp = recv_EMData(main_node_eve, tag_fftvol_eve)
		fftvol += fftvol_tmp
		fftvol_tmp = None

		weight = recv_EMData(main_node_odd, tag_weight_odd)
		weight_tmp = recv_EMData(main_node_eve, tag_weight_eve)
		weight += weight_tmp
		weight_tmp = None

		if not(info is None):
			info.write( 'begin recons all\n' )
			info.flush()
		volall = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry)
		send_EMData(volall, main_node_odd, tag_volall)
		if not(info is None):
			info.write( "recons and send all done\n" )
			info.flush()

		return model_blank(nx,nx,nx),None

        return model_blank(nx,nx,nx),None

def rec3D_MPI_noCTF(data, symmetry, mask3D, fsc_curve, myid, main_node = 0, rstep = 1.0, odd_start=0, eve_start=1, index = -1, info=None):
	'''
	  This function is to be called within an MPI program to do a reconstruction on a dataset kept in the memory 
	  Computes reconstruction and through odd-even, in order to get the resolution
	  if index > -1, projections should have attribute group set and only those whose group matches index will be used in the reconstruction
	    this is for multireference alignment
	'''
	import os
	from statistics import fsc_mask
	from utilities  import model_blank, reduce_EMData_to_root, get_image,send_EMData, recv_EMData
	from random import randint
	from mpi import mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	nproc = mpi_comm_size(MPI_COMM_WORLD)
        
	if nproc==1:
		assert main_node==0
		main_node_odd = main_node
		main_node_eve = main_node
		main_node_all = main_node
	elif nproc==2:
		main_node_odd = main_node
		main_node_eve = (main_node+1)%2
		main_node_all = main_node

		tag_voleve = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002
	else:
		main_node_odd = main_node
		main_node_eve = (main_node+1)%nproc
		main_node_all = (main_node+2)%nproc

		tag_voleve = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002

		tag_fftvol_odd = 1003
		tag_weight_odd = 1004
		tag_volall = 1005
 
        nx = data[0].get_xsize()

        fftvol_odd_file,weight_odd_file = prepare_recons(data, symmetry, myid, main_node_odd, odd_start, 2, index, info)
        fftvol_eve_file,weight_eve_file = prepare_recons(data, symmetry, myid, main_node_eve, eve_start, 2, index, info) 
         
	if nproc == 1:
		fftvol = get_image( fftvol_odd_file )
		weight = get_image( weight_odd_file )
		volodd = recons_from_fftvol(nx, fftvol, weight, symmetry)

		fftvol = get_image( fftvol_eve_file )
		weight = get_image( weight_eve_file )
		voleve = recons_from_fftvol(nx, fftvol, weight, symmetry)

		fscdat = fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)

		fftvol = get_image( fftvol_odd_file )
		fftvol_tmp = get_image(fftvol_eve_file)
		fftvol += fftvol_tmp
		fftvol_tmp = None

		weight = get_image( weight_odd_file )
		weight_tmp = get_image(weight_eve_file)
		weight += weight_tmp
		weight_tmp = None

		volall = recons_from_fftvol(nx, fftvol, weight, symmetry)

		import os
		os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file );
		os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file );
		return volall,fscdat
  
	elif nproc == 2:
		if myid == main_node_odd:
			fftvol = get_image( fftvol_odd_file )
			weight = get_image( weight_odd_file )
			volodd = recons_from_fftvol(nx, fftvol, weight, symmetry)
			voleve = recv_EMData(main_node_eve, tag_voleve)
			fscdat = fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)
		else:
			assert myid == main_node_eve
			fftvol = get_image( fftvol_eve_file )
			weight = get_image( weight_eve_file )
			voleve = recons_from_fftvol(nx, fftvol, weight, symmetry)
			send_EMData(voleve, main_node_odd, tag_voleve)

		if myid == main_node_odd:
			fftvol = get_image( fftvol_odd_file )
			fftvol_tmp = recv_EMData( main_node_eve, tag_fftvol_eve )
			fftvol += fftvol_tmp
			fftvol_tmp = None

			weight = get_image( weight_odd_file )
			weight_tmp = recv_EMData( main_node_eve, tag_weight_eve )
			weight += weight_tmp
			weight_tmp = None
			volall = recons_from_fftvol(nx, fftvol, weight, symmetry)
			import os
			os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file );
			return volall,fscdat
		else:
			assert myid == main_node_eve
			fftvol = get_image( fftvol_eve_file )
			send_EMData(fftvol, main_node_odd, tag_fftvol_eve )

			weight = get_image( weight_eve_file )
			send_EMData(weight, main_node_odd, tag_weight_eve )
			import os
			os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file );
			return model_blank(nx,nx,nx), None
	# cases from all other number of processors situations
	if myid == main_node_odd:
		fftvol = get_image( fftvol_odd_file )
		send_EMData(fftvol, main_node_all, tag_fftvol_odd )

		if not(info is None):
			info.write("fftvol odd sent")
			info.flush()

		weight = get_image( weight_odd_file )
		send_EMData(weight, main_node_all, tag_weight_odd )

		if not(info is None):
			info.write("weight odd sent")
			info.flush()

		volodd = recons_from_fftvol(nx, fftvol, weight, symmetry)
		voleve = recv_EMData(main_node_eve, tag_voleve)
		fscdat = fsc_mask(volodd, voleve, mask3D, rstep, fsc_curve)
		volall = recv_EMData(main_node_all, tag_volall)
		os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file );
		return volall,fscdat
                
	if myid == main_node_eve:
		fftvol = get_image( fftvol_eve_file )
		send_EMData(fftvol, main_node_all, tag_fftvol_eve )

		weight = get_image( weight_eve_file )
		send_EMData(weight, main_node_all, tag_weight_eve )

		voleve = recons_from_fftvol(nx, fftvol, weight, symmetry)
		send_EMData(voleve, main_node_odd, tag_voleve)
		os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file );

		return model_blank(nx,nx,nx), None

        
	if myid == main_node_all:
		fftvol = recv_EMData(main_node_odd, tag_fftvol_odd)
		if not(info is None):
			info.write( "fftvol odd recved" )
			info.flush()
		fftvol_tmp = recv_EMData(main_node_eve, tag_fftvol_eve)
		fftvol += fftvol_tmp
		fftvol_tmp = None

		weight = recv_EMData(main_node_odd, tag_weight_odd)
		weight_tmp = recv_EMData(main_node_eve, tag_weight_eve)
		weight += weight_tmp
		weight_tmp = None

		volall = recons_from_fftvol(nx, fftvol, weight, symmetry)
		send_EMData(volall, main_node_odd, tag_volall)

		return model_blank(nx,nx,nx),None


	return model_blank(nx,nx,nx),None
