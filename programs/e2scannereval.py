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
c2alt=0
degrad=pi/180.0

def display(img):
	img.write_image("tmploc.mrc")
	os.system("v2 tmploc.mrc")

def main():
	global tdim,pdim
	global cmp_probe,cmp_target
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] input.mrc

Helps to visually assess large images using localized power spectra. Generally
this is used with scanned images to look for position dependent MTF due to
film flatness problems or problems with the scanner optics. Boxes a grid pattern
of areas (default 256x256), calculates a power spectrum for each area, then reinserts
in the image, with a gap between them so the micrograph is still visible in the
background."""

	parser = OptionParser(usage=usage,version=EMANVERSION)

	parser.add_option("--box", "-S", type="int", help="size in pixels of the power spectra", default=256)
	parser.add_option("--norm", "-N", dest="norm", action="store_true", help="Normalize the image before analysis")

	
	(options, args) = parser.parse_args()
	if len(args)<1 : parser.error("Input file required")
	
	# read the target and probe
	target=EMData()
	target.read_image(args[0])
	target.del_attr("bitspersample")
	target.del_attr("datatype")
	if options.norm : target.process_inplace("eman1.normalize")
	sig=target.get_attr("sigma")
	
	nx=target.get_xsize();
	ny=target.get_ysize();
	
	nbx=nx/int(1.5*options.box)		# number of boxes in x
	sepx=options.box*3/2+(nx%(options.box*3/2))/nbx-1	# separation between boxes
	nby=ny/int(1.5*options.box)
	sepy=options.box*3/2+(ny%int(1.5*options.box))/nby
	
	for x in range(nbx):
		for y in range(nby):
			cl=target.get_clip(Region(x*sepx+(sepx-options.box)/2,y*sepy+(sepy-options.box)/2,options.box,options.box))
			cl.process_inplace("eman1.normalize.edgemean")
			cl.process_inplace("eman1.math.realtofft")
			cl.process_inplace("eman1.normalize.edgemean")
			try:
				cl*=(5.0*float(sig)/float(cl.get_attr("sigma")))
			except:
				pass
			target.insert_clip(cl,(x*sepx+(sepx-options.box)/2,y*sepy+(sepy-options.box)/2,0))

	target.write_image(args[0][:-3]+"eval.mrc")

if __name__ == "__main__":
    main()
