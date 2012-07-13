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

import os
import sys
import math
import time
from pprint import pprint

from EMAN2 import *

def main():
    progname = os.path.basename(sys.argv[0])
    usage = """prog [options]
    
This program runs a set of speed tests on the current machine

This program runs a set of speed tests in the current computer. It should
have at least 1 unloaded processor, and minimal i/o occuring when this
is run. It will give a single value which should be generally proportional
to how fast single particle refinement will run on a given computer. It is a 'real world' test,
in that it tests a variety of actual operations performed by a
refinement procedure. Don't compare values given by speed test in
different versions of EMAN, since the underlying routines may be
improved with time."""
    
    parser = EMArgumentParser(usage=usage,version=EMANVERSION)
    
    parser.add_argument("--slow",action="store_true",help="rtf_slow alignment",default=False)
    parser.add_argument("--best",action="store_true",help="rtf_best alignment",default=False)
    parser.add_argument("--low",action="store_true",help="low level test",default=False)
    parser.add_argument("--refine",action="store_true",help="refine alignment",default=False)
    parser.add_argument("--big",action="store_true",help="big size test",default=False)
    parser.add_argument("--size",type=int,help="Size of particles, 96 default for comparisons",default=96)
    parser.add_argument("--ppid", type=int, help="Set the PID of the parent process, used for cross platform PPID",default=-1)
    parser.add_argument("--verbose", "-v", dest="verbose", action="store", metavar="n", type=int, default=0, help="verbose level [0-9], higner number means higher level of verboseness")
    
    (options, args) = parser.parse_args()
    
    SIZE = options.size
    NTT = 500
    
    print 'This could take a few minutes. Please be patient.'
    if options.big:
        SIZE = 256
        
    print 'Initializing'
    
#    pat = EMData();
#    pat.set_size(SIZE, SIZE, 1)
#    for i in xrange(-SIZE/2, SIZE/2):
#        for j in xrange(-SIZE/2, SIZE/2):
#            value = -3.0 * math.exp(-Util.square(math.fabs(i)+math.fabs(j)) / 10.0) + math.exp(-Util.square( (math.fabs(i)+math.fabs(j))/2.0 )/100.0) * 2.0 if abs(i)<2 else 1.0  
#            pat.set_value_at(i+SIZE/2, j+SIZE/2, value)
#    pat.update()
    pat=test_image(size=(SIZE,SIZE))
    pat.process_inplace('normalize.circlemean')
    pat.process_inplace("mask.sharp", {"outer_radius":pat.get_xsize()/2.0})
    
    data = [None for i in xrange(NTT)]
    
    for i in xrange(NTT):
#        data[i] = test_image
#	pat.copy()
        
#        for j in xrange(SIZE):
#            for k in xrange(SIZE):
#                data[i].set_value_at_fast(j, k, Util.get_gauss_rand(0, 1.0))
#        data[i].update()
        data[i]=test_image(0,size=(SIZE,SIZE))
	data[i].add(test_image(1,size=(SIZE,SIZE)))
        data[i].process_inplace('normalize.circlemean')
        data[i].process_inplace('mask.sharp', {'outer_radius':data[i].get_xsize()/2})
        
#        if i < 5 :
#            data[i].write_image('speed.hed', i, EMUtil.ImageType.IMAGE_IMAGIC)
            
    if options.low:
        print 'Low level tests starting. Please note that compiling with optimization may \
invalidate certain tests. Also note that overhead is difficult to compensate for, \
so in most cases it is not dealt with.'
        t1 = time.clock()
        for fj in xrange(500):
            for i in xrange(NTT/2):
                data[i].dot(data[i + NTT / 2])
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 1: %d, %d x %d dot()s in %1.1f sec  %1.1f/sec-> ~%1.2f mflops' % \
            ( 500 * NTT / 2, SIZE, SIZE, ti, 500 * NTT / (2.0 * ti), SIZE * SIZE * 4 * 500.0 * NTT / (1000000.0 * ti))
        
        t1 = time.clock()
        for fj in xrange(500):
            for i in xrange(NTT/2):
                data[1].dot(data[12])
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 1a: %d, %d x %d optimized cached dot()s in %1.1f s %1.1f/s-> ~%1.2f mflops' % \
            (500 * NTT / 2, SIZE, SIZE, ti, 500 * NTT / (2.0 * ti), SIZE * SIZE * 4 * 500.0 * NTT / (1000000.0 * ti))
            
        t1 = time.clock()
        for j in xrange(500):
            for i in xrange(NTT/2):
                d = {}
                d["keepzero"] = 1
                data[i].cmp("sqeuclidean", data[i + NTT / 2], d)
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 2: %d, %d x %d lcmp()s in %1.1f sec   %1.1f/sec' % \
            (500 * NTT / 2, SIZE, SIZE, ti, 500 * NTT / (2.0 * ti))
            
        t1 = time.clock()
        for j in xrange(100):
            for i in xrange(NTT/2):
                data[i].cmp("phase", data[i + NTT / 2], {})
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 3: %d, %d x %d pcmp()s in %1.1f sec  %1.1f/sec' % \
            (100 * NTT / 2, SIZE, SIZE, ti, 100 * NTT / (2.0 * ti))
            
        t1 = time.clock()
        for j in xrange(100):
            for i in xrange(NTT/2):
                data[i].cmp("frc", data[i + NTT / 2], {})
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 4: %d, %d x %d fscmp()s in %1.1f sec  %1.1f/sec' % \
            (100 * NTT / 2, SIZE, SIZE, ti, 100 * NTT / (2.0 * ti))
            
        t1 = time.clock()
        for j in xrange(500):
            for i in xrange(NTT/2):
                data[i].process_inplace("math.absvalue")
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5a: %d, %d x %d fabs in %1.1f sec -> ~%1.2f mfabs/sec' %  \
            (500 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 500.0 * NTT / (1000000.0 * ti))
            
        t1 = time.clock()
        for j in xrange(100):
            for i in xrange(NTT/2):
                data[i].process_inplace("math.sqrt")
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5b: %d, %d x %d sqrts in %1.1f sec -> ~%1.2f msqrt/sec' % \
            (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 100.0 * NTT / (1000000.0 * ti))
        
        t1 = time.clock()
        dat = data[0].get_2dview()
        for j in xrange(100):
            for i in xrange(NTT/2):
                for m in xrange(SIZE):
                    for n in xrange(SIZE):
                        math.sqrt(dat[m][n])
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5c: %d, %d x %d sqrts in %1.1f sec -> ~%1.2f msqrt/sec (cached)' % \
            (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 100.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        d = data[0].get_2dview()
        t1 = time.clock()
        for j in xrange(100):
            for i in xrange(NTT/2):
                for m in xrange(SIZE):
                    for n in xrange(SIZE):
                        math.cos(d[m][n])
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5d: %d, %d x %d cos in %1.1f sec -> ~%1.2f mcos/sec (cached)' % \
            (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 100.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        d = data[0].get_2dview()
        t1 = time.clock()
        for j in xrange(100):
            for i in xrange(NTT/2):
                for m in xrange(SIZE-1):
                    for n in xrange(SIZE-1):
                        math.hypot(d[m][n], d[m+1][n+1])
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5e: %d, %d x %d hypot in %1.1f sec -> ~%1.2f mhypot/sec (cached)' % \
               (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 100.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        d = data[0].get_2dview()
        t1 = time.clock()
        for j in xrange(1000):
            for i in xrange(NTT/2):
                for m in xrange(SIZE-1):
                    for n in xrange(SIZE-1):
                        f = d[m][n] + d[m+1][n+1]
                        f = f + f
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5f: %d, %d x %d mult in %1.1f sec -> ~%1.2f mmult/sec (cached)' % \
               (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 1000.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        d = data[0].get_2dview()
        t1 = time.clock()
        for j in xrange(500):
            for i in xrange(NTT/2):
                for m in xrange(SIZE-1):
                    for n in xrange(SIZE-1):
                        a = d[m][n] / d[m+1][n+1]
                        a = a + a
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5g: %d, %d x %d div in %1.1f sec -> ~%1.2f mdiv/sec (cached)' % \
               (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 500.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        d = data[0].get_2dview()
        t1 = time.clock()
        for j in xrange(500):
            for i in xrange(NTT/2):
                for m in xrange(SIZE):
                    for n in xrange(SIZE):
                        f = math.fabs(d[m][n])
                        f = f + f
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5h: %d, %d x %d fabs in %1.1f sec -> ~%1.2f fabs/sec (cached)' % \
               (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 500.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        d = data[0].get_2dview()
        t1 = time.clock()
        for j in xrange(500):
            for i in xrange(NTT/2):
                for m in xrange(SIZE-1):
                    for n in xrange(SIZE-1):
                        math.atan2(d[m][n], d[m+1][n+1])
                        math.hypot(d[m][n], d[m+1][n+1])
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 5i: %d, %d x %d ri2ap in %1.1f sec -> ~%1.2f ri2ap/sec (cached)' % \
               (100 * NTT / 2, SIZE, SIZE, ti, SIZE * SIZE * 500.0 * NTT / (1000000.0 * ti))
        data[0].update()
        
        t1 = time.clock()
        for i in xrange(NTT*100):
            cp = data[i%NTT].copy()
            d = {}
            d['n'] = 2
            cp.process_inplace('math.meanshrink',d)
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 6:  %1.1f sec %f meanshrink x 2/sec' % (ti, NTT * 100.0 / ti)
        
        dla = data[0].copy()
        t1 = time.clock()
        for i in xrange(NTT*1000):
            dla.do_fft_inplace()
            dla.update()
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 7:  %1.1f sec %f ffts/sec' % (ti, NTT * 1000 / ti)
        
        dla = data[0].copy()
        t1 = time.clock()
        for i in xrange(NTT*1000):
            dla.translate(-1,-3,0)
        t2 = time.clock()
        ti = t2-t1
        print 'Baseline 8:  %1.1f sec   %f translates/sec' % (ti, NTT * 1000 / ti)
        
        return
        
    t1 = time.clock()
    for i in xrange(3):
        for j in xrange(5, NTT):
            if options.best:
                tmp = data[i].align('rtf_best', data[j], {"flip":None, "maxshift":SIZE/8})
            elif options.slow:
                tmp = data[i].align('rtf_slow', data[j], {"flip":None, "maxshift":SIZE/8})
            elif options.refine:
                tmp = data[i].align('rotate_translate_flip', data[j], {})
            else:
                tmp = data[i].align('rotate_translate_flip', data[j], {})
            
            if j%10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
        print
    t2 = time.clock()
    
    ti = t2 - t1
    
    if SIZE==96:
        print 'For comparison (note these numbers are PER CORE. ie - for a quad core machine -> x4)'
        print 'An AMD Athlon (32 bit) 900Mhz SF --------------------------------  360'
        print 'An AMD Athlon XP 2400+ (32 bit) 2.0Ghz SF ----------------------- 1010'
        print 'An AMD Athlon XP 2600+ (32 bit) 2.0Ghz SF ----------------------- 1090'
        print 'An AMD Athlon 64 3700+ 2.2Ghz SF -------------------------------- 1530'
        print 'An AMD Athlon 64 FX-51 2.2Ghz SF -------------------------------- 1760'
        print 'An AMD Opteron 248 2.2Ghz SF ------------------------------------ 1870'
        print 'An AMD Athlon 64 X2 3800+ 2.0Ghz SF ----------------------------- 1578 (2 cores -> 3,160)'
        print 'An Intel Core2 T7200 2.0Ghz SF ---------------------------------- 1990 (2 cores -> 3,980)'
        print 'An AMD Opteron 280 2.4Ghz SF ------------------------------------ 2130 (2 cores -> 4,260)'
        print 'An Intel Core2 6700 2.66Ghz SF ---------------------------------- 2600 (2 cores -> 5,200)'
        print 'An Intel Core2 Duo T9400 2.53Ghz SF ----------------------------- 2730 (2 cores -> 5,460)'
        print 'An Intel Xeon E5335 2.0Ghz SF ----------------------------------- 2010 (4 cores -> 8,040)'
        print 'An Intel Xeon X5550 2.66Ghz SF ---------------------------------- 3060 (4 cores -> 12,240)'
        print 'An Intel Xeon X5450 3.0Ghz SF ----------------------------------- 3220 (4 cores -> 12,880)'
        print 'An Intel Xeon E5645 2.4Ghz SF ----------------------------------- 3600 (6 cores -> 21,600)'
        print 'An Intel Xeon X5675 3.07Ghz SF ---------------------------------- 4070 (6 cores -> 24,420)'
        print 'An Intel Core i5-2500 3.30GHz (depends on turbo) ---------------- 5560 - 6345 (4 cores -> 22,240 - 25,380)'
        print 'An Intel Xeon E5-2670 2.6Ghz SF --------------------------------- 4800 (8 cores -> 38,400)'
        print '\nConsider using --big for a more representative value with modern high resolution maps'

	if size==256:
        print 'For comparison (note these numbers are PER CORE. ie - for a quad core machine -> x4)'
        print 'An Intel Core i7-3820 3.6GHz (depends on turbo) ----------------- 610 - 650 (4 cores -> 2440 - 2600)'
        print 'An Intel Core i5-2500 3.30GHz (depends on turbo) ---------------- 720 - 820 (4 cores -> 2880 - 3280)'
        print 'An Intel Xeon X5675 3.07Ghz SF ---------------------------------- 570       (6 cores -> 3420)'
        print 'An Intel Xeon E5-2670 2.6Ghz SF --------------------------------- 600       (8 cores -> 4800)'
 
	print '\nYour machines speed factor = %1.1f\n' % (25000.0 / ti)
    print '\nThis repesents %1.2f RTFAligns/sec\n' % (3.0 * (NTT - 5.0) / ti)
       
if __name__ == "__main__":
    main()
