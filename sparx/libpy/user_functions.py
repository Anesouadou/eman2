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

#  This file contains fuctions that perform project-dependent tasks in various
#   alignment programs, for example preparation of the reference during 2D and 3D alignment
#  To write you own function, modify the existing one (for example, wei_func is a version
#   of ref_ali2d) and add the name to the factory.  Once it is done, the function can be called
#   from appropriate application, in this case "sxali2d_c.py ...  --function=wei_func
# 
from EMAN2_cppwrap import *
from global_def import *

ref_ali2d_counter = -1
def ref_ali2d( ref_data ):
	from utilities    import print_msg
	from filter       import fit_tanh, filt_tanl
	from utilities    import center_2D
	#  Prepare the reference in 2D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FRC) to reference image:
	global  ref_ali2d_counter
	ref_ali2d_counter += 1
	print_msg("ref_ali2d   #%6d\n"%(ref_ali2d_counter))
	fl, aa = fit_tanh(ref_data[3])
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	tavg = filt_tanl(ref_data[2], fl, aa)
	cs = [0.0]*2
	tavg, cs[0], cs[1] = center_2D(tavg, ref_data[1])
	if(ref_data[1] > 0):
		msg = "Center x =      %10.3f        Center y       = %10.3f\n"%(cs[0], cs[1])
		print_msg(msg)
	return  tavg, cs


def ref_ali2d_c( ref_data ):
	from utilities    import print_msg
	from filter       import fit_tanh, filt_tanl
	from utilities    import center_2D
	#  Prepare the reference in 2D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FRC) to reference image:
	global  ref_ali2d_counter
	ref_ali2d_counter += 1
	print_msg("ref_ali2d   #%6d\n"%(ref_ali2d_counter))
	fl = min(0.1+ref_ali2d_counter*0.01, 0.4)
	aa = 0.1
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	tavg = filt_tanl(ref_data[2], fl, aa)
	cs = [0.0]*2
	tavg, cs[0], cs[1] = center_2D(tavg, ref_data[1])
	if(ref_data[1] > 0):
		msg = "Center x =      %10.3f        Center y       = %10.3f\n"%(cs[0], cs[1])
		print_msg(msg)
	return  tavg, cs


def ref_ali2d_m( ref_data ):
	from utilities    import print_msg
	from filter       import fit_tanh, filt_tanl
	from utilities    import center_2D
	#  Prepare the reference in 2D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FRC) to reference image:
	global  ref_ali2d_counter
	ref_ali2d_counter += 1
	print_msg("ref_ali2d   #%6d\n"%(ref_ali2d_counter))
	fl = 0.25
	aa = 0.1
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	tavg = filt_tanl(ref_data[2], fl, aa)
	cs = [0.0]*2
	tavg, cs[0], cs[1] = center_2D(tavg, ref_data[1])
	if(ref_data[1] > 0):
		msg = "Center x =      %10.3f        Center y       = %10.3f\n"%(cs[0], cs[1])
		print_msg(msg)
	return  tavg, cs


def ref_ali3dm( refdata ):
	from filter import fit_tanh, filt_tanl
	from utilities import get_im
	from fundamentals import rot_shift3D

	numref = refdata[0]
	outdir = refdata[1]
	fscc   = refdata[2]
	total_iter = refdata[3]
	varf   = refdata[4]



	'''
	flmin = 1.0
	flmax = -1.0
	for iref in xrange(numref):
		fl, aa = fit_tanh( fscc[iref] )
		if (fl < flmin):
			flmin = fl
			aamin = aa
		if (fl > flmax):
			flmax = fl
			aamax = aa
		# filter to minimum resolution
	'''
	print 'filter every volume at (0.4, 0.1)'
	for iref in xrange(numref):
		v = get_im(os.path.join(outdir, "vol%04d.hdf"%(total_iter)), iref)
		v = filt_tanl(v, 0.4, 0.1)
		if not(varf is None):
			print 'filtering by fourier variance'
			v.filter_by_image( varf )
		v.write_image(os.path.join(outdir, "volf%04d.hdf"%( total_iter)), iref)
					

def ref_ali3dm_ali_50S( refdata ):
	from filter import fit_tanh, filt_tanl
	from utilities import get_im
	from fundamentals import rot_shift3D

	numref = refdata[0]
	outdir = refdata[1]
	fscc   = refdata[2]
	total_iter = refdata[3]
	varf   = refdata[4]

	#mask_50S = get_im( "mask-50S.spi" )

	flmin = 1.0
	flmax = -1.0
	for iref in xrange(numref):
		fl, aa = fit_tanh( fscc[iref] )
		if (fl < flmin):
			flmin = fl
			aamin = aa
		if (fl > flmax):
			flmax = fl
			aamax = aa
		print 'iref,fl,aa: ', iref, fl, aa
		# filter to minimum resolution
	print 'flmin,aamin:', flmin, aamin
	for iref in xrange(numref):
		v = get_im(os.path.join(outdir, "vol%04d.hdf"%(total_iter)), iref)
		v = filt_tanl(v, flmin, aamin)
		'''
		if iref==0:
			v50S_0 = v.copy()
			v50S_0 *= mask_50S
		else:
			from applications import ali_vol_3
			v50S_i = v.copy()
			v50S_i *= mask_50S

			print "aligning ", iref
			params = ali_vol_3(v50S_i, v50S_0, 10.0, 0.5, mask=mask_50S)
			v = rot_shift3D( v, params[0], params[1], params[2], params[3], params[4], params[5], 1.0)
		'''
		if not(varf is None):
			print 'filtering by fourier variance'
			v.filter_by_image( varf )
	
		v.write_image(os.path.join(outdir, "volf%04d.hdf"%( total_iter)), iref)
	

def ref_random( ref_data ):
	from utilities    import print_msg
	from filter       import fit_tanh, filt_tanl
	from utilities    import center_2D
	#  Prepare the reference in 2D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FRC) to reference image:
	global  ref_ali2d_counter
	ref_ali2d_counter += 1
	print_msg("ref_ali2d   #%6d\n"%(ref_ali2d_counter))
	"""
	fl, aa = fit_tanh(ref_data[3])
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	tavg = filt_tanl(ref_data[2], fl, aa)
	"""	
	# ONE CAN USE BUTTERWORTH FILTER
	#lowfq, highfq = filt_params( ref_data[3], low = 0.1)
	#tavg  = filt_btwl( ref_data[2], lowfq, highfq)
	#msg = "Low frequency = %10.3f        High frequency = %10.3f\n"%(lowfq, highfq)
	#print_msg(msg)
	#  ONE CAN CHANGE THE MASK AS THE PROGRAM PROGRESSES
	#from morphology import adaptive_mask
	#ref_data[0] = adaptive_mask(tavg)
	#  CENTER
	cs = [0.0]*2
	tavg, cs[0], cs[1] = center_2D(ref_data[2], ref_data[1])
	'''
	from math import exp
	nx = tavg.get_xsize()
	ft = []
	good = True
	for i in xrange(nx):
		if(good):
			ex = exp((float(i)/float(nx))**2/2.0/0.12**2)
			if(ex>100.): good = False
		ft.append(ex)
	from filter import filt_table
	tavg = filt_table(tavg, ft)
	'''
	if(ref_data[1] > 0):
		msg = "Center x =      %10.3f        Center y       = %10.3f\n"%(cs[0], cs[1])
		print_msg(msg)
	return  tavg, cs

def ref_ali3d( ref_data ):
	from utilities      import print_msg
	from filter         import fit_tanh, filt_tanl
	from fundamentals   import fshift
	from morphology     import threshold
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:

	print_msg("ref_ali3d\n")
	cs = [0.0]*3

	#filt = filt_from_fsc(fscc, 0.05)
	#vol  = filt_table(vol, filt)
	# here figure the filtration parameters and filter vol for the  next iteration
	#fl, fh = filt_params(res)
	#vol	= filt_btwl(vol, fl, fh)
	# store the filtred reference volume
	#lk = 0
	#while(res[1][lk] >0.9 and res[0][lk]<0.25):
	#	lk+=1
	#fl = res[0][lk]
	#fh = min(fl+0.1,0.49)
	#vol = filt_btwl(vol, fl, fh)
	#fl, fh = filt_params(fscc)
	#print "fl, fh, iter",fl,fh,Iter
	#vol = filt_btwl(vol, fl, fh)
	stat = Util.infomask(ref_data[2], ref_data[0], False)
	volf = ref_data[2] - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])
	#volf = threshold(volf)
	Util.mul_img(volf, ref_data[0])
	fl, aa = fit_tanh(ref_data[3])
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)
	if ref_data[1] == 1:
		cs = volf.phase_cog()
		msg = "Center x = %10.3f        Center y = %10.3f        Center z = %10.3f\n"%(cs[0], cs[1], cs[2])
		print_msg(msg)
		volf  = fshift(volf, -cs[0], -cs[1], -cs[2])
	return  volf, cs

def reference3( ref_data ):
	from utilities      import print_msg
	from filter         import fit_tanh1, filt_tanl
	from fundamentals   import fshift
	from morphology     import threshold
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:

	print_msg("reference3\n")
	cs = [0.0]*3

	stat = Util.infomask(ref_data[2], ref_data[0], False)
	volf = ref_data[2] - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])
	#volf = threshold(volf)
	Util.mul_img(volf, ref_data[0])
	fl, aa = fit_tanh1(ref_data[3], 0.1)
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)
	if ref_data[1] == 1:
		cs = volf.phase_cog()
		msg = "Center x = %10.3f        Center y = %10.3f        Center z = %10.3f\n"%(cs[0], cs[1], cs[2])
		print_msg(msg)
		volf  = fshift(volf, -cs[0], -cs[1], -cs[2])
	return  volf, cs

def reference4( ref_data ):
	from utilities      import print_msg
	from filter         import fit_tanh, filt_tanl
	from fundamentals   import fshift
	from morphology     import threshold
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:

	print_msg("reference4\n")
	cs = [0.0]*3

	stat = Util.infomask(ref_data[2], ref_data[0], False)
	volf = ref_data[2] - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])
	#volf = threshold(volf)
	#Util.mul_img(volf, ref_data[0])
	#fl, aa = fit_tanh(ref_data[3])
	fl = 0.20
	aa = 0.1
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)
	if ref_data[1] == 1:
		cs = volf.phase_cog()
		msg = "Center x = %10.3f        Center y = %10.3f        Center z = %10.3f\n"%(cs[0], cs[1], cs[2])
		print_msg(msg)
		volf  = fshift(volf, -cs[0], -cs[1], -cs[2])
	return  volf, cs

def ref_aliB_cone( ref_data ):
	from utilities      import print_msg
	from filter         import fit_tanh, filt_tanl
	from fundamentals   import fshift
	from morphology     import threshold
	from math           import sqrt
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - reference PW
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:

	print_msg("ref_aliB_cone\n")
	#cs = [0.0]*3

	stat = Util.infomask(ref_data[2], None, True)
	volf = ref_data[2] - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])

	volf = threshold(volf)
	Util.mul_img(volf, ref_data[0])

	from  fundamentals  import  rops_table
	pwem = rops_table(volf)
	ftb = []
	for idum in xrange(len(pwem)):
		ftb.append(sqrt(ref_data[1][idum]/pwem[idum]))
	from filter import filt_table
	volf = filt_table(volf, ftb)

	fl, aa = fit_tanh(ref_data[3])
	#fl = 0.41
	#aa = 0.15
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)
	stat = Util.infomask(volf, None, True)
	volf -= stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])
	"""
	if(ref_data[1] == 1):
		cs    = volf.phase_cog()
		msg = "Center x = %10.3f        Center y = %10.3f        Center z = %10.3f\n"%(cs[0], cs[1], cs[2])
		print_msg(msg)
		volf  = fshift(volf, -cs[0], -cs[1], -cs[2])
	"""
	return  volf


def ref_7grp( ref_data ):
	from utilities      import print_msg
	from filter         import fit_tanh, filt_tanl, filt_gaussinv
	from fundamentals   import fshift
	from morphology     import threshold
	from math           import sqrt
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:
	#cs = [0.0]*3

	stat = Util.infomask(ref_data[2], None, False)
	volf = ref_data[2] - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])
	volf = Util.muln_img(threshold(volf), ref_data[0])

	fl, aa = fit_tanh(ref_data[3])
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)
	if(ref_data[1] == 1):
		cs    = volf.phase_cog()
		msg = "Center x =	%10.3f        Center y       = %10.3f        Center z       = %10.3f\n"%(cs[0], cs[1], cs[2])
		print_msg(msg)
		volf  = fshift(volf, -cs[0], -cs[1], -cs[2])
	B_factor = 10.0
	volf = filt_gaussinv( volf, 10.0 )
	return  volf,cs

def spruce_up( ref_data ):
	from utilities      import print_msg
	from filter         import filt_tanl, fit_tanh
	from morphology     import threshold
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:

	print_msg("Changed4 spruce_up\n")
	cs = [0.0]*3

	stat = Util.infomask(ref_data[2], None, True)
	volf = ref_data[2] - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])
	volf = threshold(volf)
	# Apply B-factor
	from filter import filt_gaussinv
	from math import sqrt
	B = 1.0/sqrt(2.*14.0)
	volf = filt_gaussinv(volf, B, False)
	nx = volf.get_xsize()
	from utilities import model_circle
	stat = Util.infomask(volf, model_circle(nx//2-2,nx,nx,nx)-model_circle(nx//2-6,nx,nx,nx), True)

	volf -= stat[0]
	Util.mul_img(volf, ref_data[0])
	fl, aa = fit_tanh(ref_data[3])
	#fl = 0.35
	#aa = 0.1
	aa /= 2
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)
	return  volf, cs

def spruce_up_variance( ref_data ):
	from utilities      import print_msg
	from filter         import filt_tanl, fit_tanh, filt_gaussl
	from morphology     import threshold
	#  Prepare the reference in 3D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#   4 1.0/variance
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FSC) to reference image:

	print_msg("spruce_up with variance\n")
	cs = [0.0]*3

	volf = ref_data[2].filter_by_image(ref_data[4])

	fl, aa = fit_tanh(ref_data[3])
	#fl = 0.35
	#aa = 0.1
	aa /= 2
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	volf = filt_tanl(volf, fl, aa)

	stat = Util.infomask(volf, None, True)
	volf = volf - stat[0]
	Util.mul_scalar(volf, 1.0/stat[1])

	from utilities import model_circle
	nx = volf.get_xsize()
	stat = Util.infomask(volf, model_circle(nx//2-2,nx,nx,nx)-model_circle(nx//2-6,nx,nx,nx), True)

	volf -= stat[0]
	Util.mul_img(volf, ref_data[0])

	volf = threshold(volf)
	# The next line is to smooth edges
	volf = filt_gaussl(volf, 0.4)
	if(ref_data[1] == 1):
		from fundamentals   import fshift
		cs    = volf.phase_cog()
		msg = "Center x =	%10.3f  y = %10.3f  z = %10.3f\n"%(cs[0], cs[1], cs[2])
		print_msg(msg)
		volf  = fshift(volf, -cs[0], -cs[1], -cs[2])
	return  volf, cs

def steady( ref_data ):
	from utilities    import print_msg
	from filter       import fit_tanh, filt_tanl
	from utilities    import center_2D
	#  Prepare the reference in 2D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FRC) to reference image:
	global  ref_ali2d_counter
	ref_ali2d_counter += 1
	print_msg("steady   #%6d\n"%(ref_ali2d_counter))
	fl = 0.12 + (ref_ali2d_counter//3)*0.1
	aa = 0.1
	msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	print_msg(msg)
	tavg = filt_tanl(ref_data[2], fl, aa)
	cs = [0.0]*2
	return  tavg, cs

def constant( ref_data ):
	from utilities    import print_msg
	from filter       import fit_tanh, filt_tanl
	from utilities    import center_2D
	#  Prepare the reference in 2D alignment, i.e., low-pass filter and center.
	#  Input: list ref_data
	#   0 - mask
	#   1 - center flag
	#   2 - raw average
	#   3 - fsc result
	#  Output: filtered, centered, and masked reference image
	#  apply filtration (FRC) to reference image:
	global  ref_ali2d_counter
	ref_ali2d_counter += 1
	#print_msg("steady   #%6d\n"%(ref_ali2d_counter))
	fl = 0.4
	aa = 0.1
	#msg = "Tangent filter:  cut-off frequency = %10.3f        fall-off = %10.3f\n"%(fl, aa)
	#print_msg(msg)
	tavg = filt_tanl(ref_data[2], fl, aa)
	cs = [0.0]*2
	return  tavg, cs

# rewrote factory dict to provide a flexible interface for providing user functions dynamically.
#    factory is a class that checks how it's called. static labels are rerouted to the original
#    functions, new are are routed to build_user_function (provided below), to load from file
#    and pathname settings....
# Note: this is a workaround to provide backwards compatibility and to avoid rewriting all functions
#    using user_functions. this can be removed when this is no longer necessary....

class factory_class:

	def __init__(self):
		self.contents = {}
		self.contents["ref_ali2d"]          = ref_ali2d
		self.contents["ref_ali2d_c"]        = ref_ali2d_c
		self.contents["ref_ali2d_m"]        = ref_ali2d_m
		self.contents["ref_random"]         = ref_random
		self.contents["ref_ali3d"]          = ref_ali3d
		self.contents["ref_ali3dm"]         = ref_ali3dm
		self.contents["ref_ali3dm_ali_50S"] = ref_ali3dm_ali_50S
		self.contents["reference3"]         = reference3
		self.contents["reference4"]         = reference4
		self.contents["spruce_up"]          = spruce_up
		self.contents["spruce_up_variance"] = spruce_up_variance
		self.contents["ref_aliB_cone"]      = ref_aliB_cone
		self.contents["ref_7grp"]           = ref_7grp
		self.contents["steady"]             = steady
		self.contents["constant"]           = constant
		
	def __getitem__(self,index):

		if (type(index) is str):
			try:
				return self.contents[index]
			except KeyError:
				return None
			except:
				return None
		if (type(index) is list):
			try:
				# try building with module, function and path
				return build_user_function(module_name=index[0],function_name=index[1],
							   path_name=index[2])
			except IndexError:
				# we probably have a list [module,function] only, no path
				return build_user_function(module_name=index[0],function_name=index[1])
			except:
				# the parameter is something we can't understand... return None or
				#    raise an exception....
				return None

		print type(index)
		return None
	

factory=factory_class()
						   
# build_user_function: instead of a static user function factory that has to be updated for
#    every change, we use the imp import mechanism: a module can be supplied at runtime (as
#    an argument of the function), which will be imported. from that modules we try to import
#    the function (function name is supplied as a second argument). this function object is
#    returned to the caller.
# Note that the returned function (at this time) does not support dynamic argument lists,
#    so the interface of the function (i.e. number of arguments and the way that they are used)
#    has to be known and is static!

def build_user_function(module_name=None,function_name=None,path_name=None):

	if (module_name is None) or (function_name is None):
		return None

	# set default path list here. this can be extended to include user directories, for
	#    instance $HOME,$HOME/sparx. list is necessary, since find_module expects a list
	#    of paths to try as second argument
	import os
	if (path_name is None):
		path_list = [os.path.expanduser("~"),os.path.expanduser("~")+os.sep+"sparx",]

	if (type(path_name) is list):
		path_list = path_name

	if (type(path_name) is str):
		path_list = [path_name,]

	import imp

	try:
		(file,path,descript) = imp.find_module(module_name,path_list)
	except ImportError:
		print "could not find module "+str(module_name)+" in path "+str(path_name)
		return None

	try:
		dynamic_mod = imp.load_module(module_name,file,path,descript)
	except ImportError:
		print "could not load module "+str(module_name)+" in path "+str(path)
		return None
		
	# function name has to be taken from dict, since otherwise we would be trying an
	#    equivalent of "import dynamic_mod.function_name"
	try:
		dynamic_func = dynamic_mod.__dict__[function_name]
	except KeyError:
		# key error means function is not defined in the module....
		print "could not import user function "+str(function_name)+" from module"
		print str(path)
		return None
	except:
		print "unknown error getting function!"
		return None
	else:
		return dynamic_func

	
	
