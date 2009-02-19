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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#
#

import sys
from sys import exit
import os
import time
import shelve
import re
import cPickle
import zlib
import socket
from EMAN2_cppwrap import *
from pyemtbx.imagetypes import *
from pyemtbx.box import *
#from Sparx import *

EMANVERSION="EMAN2 v1.97"

HOMEDB=None

# This block attempts to open the standard EMAN2 database interface
# if it fails, it sets db to None. Applications can then alter their
# behavior appropriately
#try:
import EMAN2db
from EMAN2db import EMAN2DB,db_open_dict,db_close_dict,db_remove_dict,db_list_dicts,db_check_dict,db_parse_path
#except:
#	HOMEDB=None

Vec3f.__str__=lambda x:"Vec3f"+str(x.as_list())

# Who is using this? Transform3D is deprecated use the Transform insteand
Transform3D.__str__=lambda x:"Transform3D(\t%7.4g\t%7.4g\t%7.4g\n\t\t%7.4g\t%7.4g\t%7.4g\n\t\t%7.4g\t%7.4g\t%7.4g)\nPretrans:%s\nPosttrans:%s"%(x.at(0,0),x.at(0,1),x.at(0,2),x.at(1,0),x.at(1,1),x.at(1,2),x.at(2,0),x.at(2,1),x.at(2,2),str(x.get_pretrans()),str(x.get_posttrans()))

GUIMode=0
app = 0
GUIbeingdragged=None

glut_inited = False


# Aliases
EMData.get=EMData.get_value_at
EMData.set=EMData.set_value_at

def emdata_to_string(self):
	"""This returns a compressed string representation of the EMData object, suitable for storage
	or network communication. The EMData object is pickled, then compressed wth zlib. Restore with
	static method from_string()."""
	return zlib.compress(cPickle.dumps(self,-1),3)	# we use a lower compression mode for speed
	
def emdata_from_string(s):
	"""This will restore a serialized compressed EMData object as prepared by as_string()"""
	return cPickle.loads(zlib.decompress(s))

EMData.from_string=emdata_from_string
EMData.to_string=emdata_to_string

def timer(fn,n=1):
	a=time.time()
	for i in range(n): fn()
	print time.time()-a

def E2init(argv) :
	"""E2init(argv)
This function is called to log information about the current job to the local logfile. The flags stored for each process
are pid, start, args, progress and end. progress is from 0.0-1.0 and may or may not be updated. end is not set until the process
is complete. If the process is killed, 'end' may never be set."""
	if EMAN2db.MPIMODE :
		print "Note: Running in MPI mode, history database disabled"
		return
	
	global HOMEDB
	HOMEDB=EMAN2db.EMAN2DB.open_db()
	HOMEDB.open_dict("history")
	if HOMEDB != None:
		if not HOMEDB.history.has_key("count") : HOMEDB.history["count"]=1
		else : HOMEDB.history["count"]+=1
		n=HOMEDB.history["count"]
		HOMEDB.history[n]={"host":socket.gethostname(),"pid":os.getpid(),"start":time.time(),"args":argv,"path":os.getcwd()}
	else:
		print "Warning: EMAN2 missing BDB support"
		try:
			sdb=shelve.open(".eman2log")
		except:
			return -1
		
		try:
			n=sdb["count"]
			sdb["count"]=n+1
		except:
			n=1
			sdb["count"]=n
		sdb[str(n)]={"pid":os.getpid(),"start":time.time(),"args":argv,"progress":0.0}
		sdb.close()

	return n

def E2progress(n,progress):
	"""Updates the progress fraction (0.0-1.0) for a running job. Negative values may optionally be
set to indicate an error exit."""
	if EMAN2db.MPIMODE : return

	global HOMEDB
	
	if HOMEDB :
		d=HOMEDB.history[n]
		d["progress"]=progress
		HOMEDB.history[n]=d
	else :
		db=shelve.open(".eman2log")
		d=db[str(n)]
		d["progress"]=progress
		db[str(n)]=d
	
	return n
	

def E2end(n):
	"""E2end(n)
This function is called to log the end of the current job. n is returned by E2init"""
	if EMAN2db.MPIMODE : return

	global HOMEDB
	
	if HOMEDB :
		d=HOMEDB.history[n]
		d["end"]=time.time()
		d["progress"]=1.0
		HOMEDB.history[n]=d
		HOMEDB.close_dict("history")
	else :
		db=shelve.open(".eman2log")
		d=db[str(n)]
		d["end"]=time.time()
		d["progress"]=1.0
		db[str(n)]=d
		db.close()
	
	return n

def E2saveappwin(app,key,win):
	"""stores the window geometry using the application default mechanism for later restoration. Note that
	this will only work with Qt windows"""
	pos=win.pos()
	sz=win.size()
	geom=(pos.x(),pos.y(),win.width(),win.height())
	E2setappval(app,key,geom)
	
def E2loadappwin(app,key,win):
	"""restores a geometry saved with E2saveappwin"""
	geom=E2getappval(app,key)
	win.resize(geom[2],geom[3])
	win.move(geom[0],geom[1])

def E2setappval(app,key,value):
	"""E2setappval
This function will set an application default value both in the local directory and ~/.eman2
When settings are read, the local value is checked first, then if necessary, the global value."""
	try:
		app.replace(".","_")
		key.replace(".","_")
	except: 
		print "Error with E2setappval, app and key must be strings"
		return
	
	try:
		db=shelve.open(".eman2settings")
		db[app+"."+key]=value
		db.close()
	except:
		pass

	try:
		dir=e2gethome()
		dir+="/.eman2"
		os.mkdir(dir)
	except:
		return
		
	try:
		db=shelve.open(dir+"/appdefaults")
		db[app+"."+key]=value
		db.close()
	except:
		return


def E2getappval(app,key):
	"""E2getappval
This function will get an application default by first checking the local directory, followed by
~/.eman2"""
	try:
		app.replace(".","_")
		key.replace(".","_")
	except: 
		print "Error with E2getappval, app and key must be strings"
		return None
	
	try:
		db=shelve.open(".eman2settings")
		ret=db[app+"."+key]
		db.close()
		return ret
	except:
		pass
	
	try:
		dir=e2gethome()
		dir+="/.eman2"
		db=shelve.open(dir+"/appdefaults")
		ret=db[app+"."+key]
		db.close()

		return ret
	except: pass
	
	return None


def e2getinstalldir() :
	"""platform independent path with '/'"""
	if(sys.platform != 'win32'):
		url=os.getenv("EMAN2DIR")
	else:
		url=os.getenv("EMAN2DIR")
		url=url.replace("\\","/")
	return url

def e2gethome() :
	"""platform independent path with '/'"""
	if(sys.platform != 'win32'):
		url=os.getenv("HOME")
	else:
		url=os.getenv("HOMEPATH")
		url=url.replace("\\","/")
	return url

def e2getcwd() :
	"""platform independent path with '/'"""
	url=os.getcwd()
	url=url.replace("\\","/")
	return url

def numbered_path(prefix,makenew):
	"""Finds the next numbered path to use for a given prefix. ie- prefix='refine' if refine_01/EMAN2DB 
exists will produce refine_02 if makenew is set (and create refine_02) and refine_01 if not"""
	n=1
	while os.access("%s_%02d/EMAN2DB"%(prefix,n),os.F_OK) : n+=1
	if makenew or n==1:
		path="%s_%02d"%(prefix,n)
		try: os.mkdir(path)
		except: pass
		return path
	return "%s_%02d"%(prefix,n-1)

def get_numbered_directories(prefix,wd=e2getcwd()):
	'''
	Gets the numbered directories starting with prefix in the given working directory (wd)
	A prefix example would be "refine_" or "r2d_" etc. Used originally form within the workflow context
	'''
	dirs, files = get_files_and_directories(wd)
	dirs.sort()
	l = len(prefix) 
	for i in range(len(dirs)-1,-1,-1):
		if len(dirs[i]) != l+2:# plus two because we only check for two numbered directories
			dirs.pop(i)
		elif dirs[i][:l] != prefix:
			dirs.pop(i)
		else:
			try: int(dirs[i][l:])
			except: dirs.pop(i)
	
	# allright everything left in dirs is "refine_??" where the ?? is castable to an int, so we should be safe now
	
	return dirs

def get_image_directory():
	pf = get_platform()
	dtag = get_dtag()
	if pf != "Windows":
		return os.getenv("EMAN2DIR")+ dtag + "images" + dtag + "macimages" + dtag 
	else:
		return os.getenv("EMAN2DIR")+ dtag + "images" + dtag
	
def get_dtag():
#	pfrm = get_platform()
#	if pfrm == "Windows": return "\\"
#	else: return "/"
	return "/"

def get_files_and_directories(path=".",include_hidden=False):
	if path == ".": l_path = "./"
	else: l_path = path
	if len(l_path) == 0: path = get_dtag()
	elif l_path[-1] not in ["/","\\"]: l_path += get_dtag() 
	
	dirs = []
	files = []
	try:
		entries = os.listdir(l_path)
	except: # something is wrong with the path
		print "path failed",l_path
		return dirs,files
	
	for name in entries:
		if len(name) == 0: continue
		if not include_hidden: 
			if name[0] == ".":
				continue
		
		try:
			if os.path.isdir(l_path+name):
				dirs.append(name)
			else:
				files.append(name)
		except:
			pass # something was wrong with the directory
	return dirs,files
		

def numbered_bdb(bdb_url):
	'''
	give something like "bdb:refine_01#class_indices (which means bdb:refine_01#class_indices_??.bdb files exist)
	
	will return the next available name bdb:refine_01#class_indices_?? (minus the bdb)
	'''
	
	useful_info = db_parse_path(bdb_url)

	d = get_dtag()
	file_name_begin = useful_info[0] + d + "EMAN2DB" + d + useful_info[1] + "_"
	  
	for i in range(0,10):
		for j in range(0,10):
			name = file_name_begin+str(i)+str(j)+".bdb"
			if os.path.exists(name): continue
			else: 
				return "bdb:"+useful_info[0]+"#"+useful_info[1] + "_"+str(i)+str(j)

def remove_image(fsp):
	"""This will remove the image file pointed to by fsp. The reason for this function
	to exist is formats like IMAGIC which store data in two files. This insures that
	both files are removed."""
	try:
		os.unlink(fsp)
		if fsp[-4:]==".hed" : os.unlink(fsp[:-3]+"img")
		elif fsp[-4:]==".img" : os.unlink(fsp[:-3]+"hed")
	except: pass

def parsesym(optstr):
	# FIXME - this function is no longer necessary since I overwrite the Symmetry3D::get function (on the c side). d.woolford
	[sym, dict] = parsemodopt(optstr)
	if sym[0] in ['c','d','h']:
		dict["nsym"] = int(sym[1:])
		sym = sym[0]

	sym = Symmetries.get(sym, dict)
	return sym

parseparmobj1=re.compile("([^\(]*)\(([^\)]*)\)")	# This parses test(n=v,n2=v2) into ("test","n=v,n2=v2")
parseparmobj2=re.compile("([^=,]*)=([^,]*)")		# This parses "n=v,n2=v2" into [("n","v"),("n2","v2")]
parseparmobj3=re.compile("[^:]\w*=*[-\w.]*") # This parses ("a:v1=2:v2=3") into ("a", "v1=2", "v2=3") 
parseparmobj4=re.compile("\w*[^=][\w.]*") # This parses ("v1=2") into ("v1", "2")
def parsemodopt(optstr):
	"""This is used so the user can provide the name of a comparator, processor, etc. with options
	in a convenient form. It will parse "dot:normalize=1:negative=0" and return
	("dot",{"normalize":1,"negative":0})"""
	
	if not optstr or len(optstr)==0 : return (None,{})
	
	p_1 = re.findall( parseparmobj3, optstr )
	if len(p_1)==0: return (optstr,{})
	
	r2 = {}
	for i in range (1, len(p_1)):
		args = re.findall( parseparmobj4, p_1[i] )
		if len(args) != 2:
			print "ERROR: Command line parameter options failed"
			print "\tSpecify parameters using this syntax - optiontype:p1=v1:p2=v2 etc"
			print "\tThe problems arguments are:"
			print args
			return (None,None)
		
		v = args[1]
		try: v=int(v)
		except:
			try: v=float(v)
			except:
				if v[0]=='"' and v[-1]=='"' : v=j[1][1:-1]
		
		r2[args[0]] = v

	return (p_1[0], r2)

parseparmobj_op = re.compile("\+=|-=|\*=|\/=|%=")
parseparmobj_logical = re.compile(">=|<=|==|~=|!=|<|>") 	# finds the logical operators <=, >=, ==, ~=, !=, <, >
parseparmobj_op_words = re.compile("\w*[^=+-\/\*%][\w.]*") # splits ("v1?2") into ("v1","2") where ? can be any combination of the characters "=!<>~"
parseparmobj_logical_words = re.compile("\w*[^=!<>~][\w.]*") # splits ("v1?2") into ("v1","2") where ? can be any combination of the characters "=!<>~"
def parsemodopt_logical(optstr):

	if not optstr or len(optstr)==0 : return (None)
	
	p_1 = re.findall( parseparmobj_logical_words, optstr )
	
	if len(p_1)==0: return (optstr,{})
	if ( len(p_1) != 2 ):
		print "ERROR: parsemodopt_logical currently only supports single logical expressions"
		print "Could not handle %s" %optstr
		return (None,None,None)
	
	p_2 = re.findall( parseparmobj_logical, optstr )
	
	if ( len(p_2) != 1 ):
		print "ERROR: could not find logical expression in %s" %optstr
		return (None,None,None)
	
	
	if ( p_2[0] not in ["==", "<=", ">=", "!=", "~=", "<", ">"] ):
		print "ERROR: parsemodopt_logical %s could not extract logical expression" %(p_2[0])
		print "Must be one of \"==\", \"<=\", \">=\", \"<\", \">\" \"!=\" or \~=\" "
		return (None,None,None)

	return (p_1[0], p_2[0], p_1[1])
	
def parsemodopt_operation(optstr):

	if not optstr or len(optstr)==0 : return (None)
	
	p_1 = re.findall( parseparmobj_op_words, optstr )
	if len(p_1)==0: return (optstr,{})
	
	if ( len(p_1) != 2 ):
		print "ERROR: parsemodopt_logical currently only supports single logical expressions"
		print "Could not handle %s" %optstr
		return (None,None,None)
	
	p_2 = re.findall( parseparmobj_op, optstr )
	if ( len(p_2) != 1 ):
		print "ERROR: could not find logical expression in %s" %optstr
		return (None,None,None)
	
	
	if ( p_2[0] not in ["+=", "-=", "*=", "/=", "%="]):
		print "ERROR: parsemodopt_logical %s could not extract logical expression" %(p_2[0])
		print "Must be one of", "+=", "-=", "*=", "/=", "%="
		return (None,None,None)

	return (p_1[0], p_2[0], p_1[1])


def display(img):
	if GUIMode:
		import emimage
		image = emimage.EMImageModule(img,None,app)
		app.show_specific(image)
		try: image.optimally_resize()
		except: pass
	else:
		# In non interactive GUI mode, this will display an image or list of images with e2display
		fsp="bdb:%s/.eman2dir#tmp"%e2gethome()
		
		db_remove_dict(fsp)
		d=db_open_dict(fsp)
		if isinstance(img,list) or isinstance(img,tuple) :
			for i,j in enumerate(img): d[i]=j
		else:
			d[0]=img
		d.close()
	#	os.system("v2 /tmp/img.hed")
		os.system("e2display.py "+fsp)
		
class EMImage(object):
	"""This is basically a factory class that will return an instance of the appropriate EMImage* class """
	def __new__(cls,data=None,old=None,parent=1):
		"""This will create a new EMImage* object depending on the type of 'data'. If
		old= is provided, and of the appropriate type, it will be used rather than creating
		a new instance."""
		if GUIMode:	
			import emimage
			image = emimage.EMImageModule(data,old,app)
			app.show_specific(image)
			try: image.optimally_resize()
			except: pass
			return image.get_qt_widget()
		else: print "can not instantiate EMImage in non gui mode"

def plot(data,show=1,size=(800,600),path="plot.png"):
	"""plots an image or an array using the matplotlib library"""
	if GUIMode:
		from emplot2d import EMPlot2DModule
		plotw=EMPlot2DModule(application=app)
		plotw.set_data("interactive",data)
		plotw.get_qt_widget().setWindowTitle("2D Plot")
		app.show_specific(plotw)
		return plotw
	else :
		import matplotlib
		matplotlib.use('Agg')
		import pylab
		pylab.figure(figsize=(size[0]/72.0,size[1]/72.0),dpi=72)
		if isinstance(data,EMData) :
			a=[]
			for i in range(data.get_xsize()): 
				a.append(data.get_value_at(i,0,0))
			pylab.plot(a)
		elif isinstance(data,list) or isinstance(data,tuple):
			if isinstance(data[0],list) or isinstance(data[0],tuple) :
				pylab.plot(data[0],data[1])
			else:
				try:
					a=float(data[0])
					pylab.plot(data)
				except:
					print "List, but data isn't floats"
					return
		else :
			print "I don't know how to plot that type"
			return
		
		pylab.savefig(path)
		if show:
			try: os.system("display "+path)
			except: pass

def kill_process(pid):
	'''
	platform independent way of killing a process 
	'''
	import os
	import platform
	platform_string = get_platform()
	if platform_string == "Windows":
		# taken from http://www.python.org/doc/faq/windows/#how-do-i-emulate-os-kill-in-windows
		import win32api
		try:
			# I _think_ this will work but could definitely be wrong
			handle = win32api.OpenProcess(1, 0, pid)
			win32api.TerminateProcess(handle,-1)
			win32api.CloseHandle(handle)
			return 1
		except:
			return 0
	else:
		try:
			os.kill(pid,1)
			return 1
		except:
			return 0

def process_running(pid):
	'''
	Platform independent way of checking if a process is running, based on the pid
	'''
	import platform
	import os
	platform_string = get_platform()
	if platform_string == "Windows":
		# taken from http://www.python.org/doc/faq/windows/#how-do-i-emulate-os-kill-in-windows
		import win32api
		try:
			# I _think_ this will work but could definitely be wrong
			handle = win32api.OpenProcess(1, 0, pid)
			#win32api.CloseHandle(handle) # is this necessary?
			return 1
		except:
			return 0
	else:
		try:
			os.kill(pid,0)
			return 1
		except:
			return 0
			
def memory_stats():
	'''
	Returns [total memory in GB,available memory in GB]
	if any errors occur while trying to retrieve either of these values their retun value is -1
	'''
	import platform
	platform_string = get_platform()
	mem_total = -1
	mem_avail = -1
	if platform_string == "Linux":
		try:
			f = open("/proc/meminfo")
			a = f.readlines()
			mt = a[0].split()
			if mt[0] == "MemTotal:":
				mem_total = float(mt[1])/1000000.0
			ma = a[1].split()
			if ma[0] == "MemFree:":
				mem_avail = float(ma[1])/1000000.0
		except:
			pass
		
	elif platform_string == "Darwin":
		import commands
		status_total, output_total = commands.getstatusoutput("sysctl hw.memsize")
		status_used, output_used = commands.getstatusoutput("sysctl hw.usermem")
		total_strings = output_total.split()
		if len(total_strings) >= 2: # try to make it future proof, the output of sysctl will have to be double checked. Let's put it in a unit test in
			total_len = len("hw.memsize")
			if total_strings[0][:total_len] == "hw.memsize":
				try:
					mem_total = float(total_strings[1])/1000000000.0 # on Mac the output value is in bytes, not kilobytes (as in Linux)
				except:pass # mem_total is just -1
		
		used_strings = output_used.split()
		mem_used = -1
		if len(used_strings) >=2:
			used_len = len("hw.usermem")
			if used_strings[0][:used_len] == "hw.usermem":
				try:
					mem_used = float(used_strings[1])/1000000000.0 # on Mac the output value is in bytes, not kilobytes (as in Linux)
				except:pass # mem_used is just -1
		
		if mem_used != -1 and mem_total != -1:
			mem_avail = mem_total - mem_used
			
	return [mem_total,mem_avail]


def num_cpus():
	'''
	Returns the number of cpus available on the current platform
	This program is in its infancy but should work in general. A very basic approach is employed for Linux,
	however MAC and Windows should work fine.
	Based on http://mail.python.org/pipermail/python-list/2007-October/460750.html
	'''
	import platform
	platform_string = get_platform()
	if platform_string == "Linux":
		try:
			f = open("/proc/cpuinfo")
			a = f.readlines()
			# assumes the entry 12 is the one we're looking for - this might not work but we can fix it as we go
			split = a[11].split()
			if split[0] == "cpu" and split[1] == "cores":
				cores = int(split[-1])
				if cores < 1: return 1 # just for safety
				else: return cores
			else:
				return 1
		except:
			return 1
	elif platform_string == "Windows":
		try:
			cores = os.getenv("NUMBER_OF_PROCESSORS")
			if cores < 1: return 1 # just for safety
			else: return cores
		except:
			return 1
	elif platform_string == "Darwin":
		import commands
		status, output = commands.getstatusoutput("sysctl hw.logicalcpu")
		strings = output.split()
		cores = 1 # this has to be true or else it's a really special computer ;)
		if len(strings) >=2:
			used_len = len("hw.logicalcpu")
			if strings[0][:used_len] == "hw.logicalcpu": # this essentially means the system call worked
				try:
					cores = int(strings[1])
				except:pass # mem_used is just -1
				
		if cores < 1: 
			print "warning, the number of cpus was negative (%i), this means the MAC system command (sysctl) has been updated and EMAN2 has not accommodated for this. Returning 1 for the number of cores." %cores
			cores = 1 # just for safety, something could have gone wrong. Maybe we should raise instead
		return cores

	else:
		print "error, in num_cpus - uknown platform string:",platform_string," - returning 1"
		return 1

def gimme_image_dimensions2D( imagefilename ):
	"""returns the dimensions of the first image in a file (2-D)"""
	
	e = EMData()
	e.read_image(imagefilename,0,True)
	return (e.get_xsize(),e.get_ysize())

# get the three dimensions of a an image
def gimme_image_dimensions3D( imagefilename ):
	
	#pdb.set_trace()
	
	read_header_only = True
	e = EMData();
	e.read_image(imagefilename,0, read_header_only)
	
	xsize = e.get_xsize()
	ysize = e.get_ysize()
	zsize = e.get_zsize()
	
	return (xsize, ysize,zsize)

def remove_file( file_name, img_couples_too=True ):
	'''
	A function for removing a file from disk. Works for database style file names.
	Adapted so that if you want to remove an img/hed couple it will automatically remove both.
	You can disable the img coupling feature with the the image_couples_too flag
	'''
	
	if ( os.path.exists(file_name) ):
		
		parts = file_name.split('.')
		
		file_tag = parts[len(parts)-1]
			
		if ( file_tag == 'hed' or file_tag == 'img' ):
			# get everything that isn't the tag
			name = ''
			for i in range(0,len(parts)-1):
				name = name + parts[i] + '.'
			
			if img_couples_too:
				os.remove(name+'hed')
				os.remove(name+'img')
			else: os.remove(name+file_tag)
		else:
			os.remove(file_name)
		return True
	elif db_check_dict(file_name):
		db_remove_dict(file_name)
	else:
		print "Warning, attempt to remove file (%s) that does not exist. No action taken." %file_name
		return False

# returns the local date and time as a string
def local_datetime(secs):
	from time import localtime
	t=localtime(secs)
	return "%04d/%02d/%02d %02d:%02d:%02d"%t[:6]

# returns gm time as a string. For example if it's 11:13 pm on the 18th of June 2008 this will return something like
# '23:13:25.14 18/6/2008'
def gm_time_string():
	'''
	Returns gm time as a string. For example if it's 11:13 pm on the 18th of June 2008 this will return something like '23:13:25.14 18-6-2008'
	The use of '/' is intentionally avoided
	'''
	
	from time import gmtime,time
	a = time()
	b = gmtime(a)
	astr = str(a)
	idx = str.find(astr,'.')
	decimalseconds = astr[idx:len(astr)]
	
	val = str(b[3])+':'+str(b[4])+':'+str(b[5])+decimalseconds +' '+str(b[2])+'-'+str(b[1])+'-'+str(b[0])
	return val

def is_2d_image_mx(filename):
	'''
	Returns true if the filename exists, is an EM image type, is 2D, and has more than one image
	'''
	if not file_exists(filename): return False, "File doesn't exist : "+filename
	
	read_header_only = True
	a = EMData()
	# this is guaranteed not to raise unless the image has been removed from disk since the last call to check_files_are_em_images
	a.read_image(filename,0,read_header_only)
	if a.get_ndim() != 2:
		return False, "Image is not 2D :", filename
	elif EMUtil.get_image_count(filename) < 2:
		return False, "Image is not a matrix :", filename
	else:
		return True, "Image is a 2D stack"

def check_files_are_2d_images(filenames):
	'''
	Checks that the files exist, are valid EM types, and are non matrix 2D images
	'''
	fine, message = check_files_are_em_images(filenames)
	if not fine:
		return fine, message
	else:
		for name in filenames:
			if EMUtil.get_image_count(name) > 1:
				return False, "Image contains more than one image :", name
			
			else:
				read_header_only = True
				a = EMData()
				# this is guaranteed not to raise unless the image has been removed from disk since the last call to check_files_are_em_images
				a.read_image(name,0,read_header_only)
				if a.get_ndim() != 2:
					return False, "Image is not 2D :", name
				
		return True, "Images are all valid and 2D"
			

def check_files_are_em_images(filenames):
	'''
	Checks a list of filenames to first verify that they exist, and secondly to verify that they are valid EM images
	Returns bool, string where bool means the filenames are good, and the string is an error message or similar
	'''
	for file in filenames:
		if not os.path.exists(file):
		  	try:
		  		is_db = db_check_dict(file)
		  		if not is_db: raise
		  	except: return False, "File doesn't exist:"+file
		  	
		read_header_only = True
		a = EMData()
		try:
			a.read_image(file,0,read_header_only)
		except:
			return False, "File is not a valid EM image:"+file
			
	return True,"images are fine"
	

def file_exists( file_name ):
	'''
	A function for checking if a file exists
	basically wraps os.path.exists, but when an img or hed file is the argument, it
	checks for the existence of both images
	Also checks if the argument is a valid dictionary
	'''
	
	if ( os.path.exists(file_name) ):
		
		parts = file_name.split('.')
		file_tag = parts[len(parts)-1]
		
		# get everything that isn't the tag
		name = ''
		for i in range(0,len(parts)-1):
			name = name + parts[i] + '.'

		if ( file_tag == 'hed' ):
			if ( not os.path.exists(name+'img') ):
				print "Warning - %s does not exist" %(name+'img')
				return False
			else: return True;
		elif (file_tag == 'img'):
			if (not os.path.exists(name+'hed')):
				print "Warning - %s does not exist" %(name+'hed')
				return False
			else: return True;
		else:
			return True
	else:
		try:
			if db_check_dict(file_name):
				return True
			else: return False
		except: return False
	
# a function for stripping a the file tag from the end of a string.
# is if given image.mrc this functions strips the '.mrc' and returns 'image'
def strip_file_tag(file_name):
	# FIXME it's probably easiest to do this with regular expressions...
	'''
	FIXME - could replace with Util.remove_filename_ext()
	'''
	for i in range(len(file_name)-1,-1,-1):
		if file_name[i] == '.':
			break
	else:
		print "never found the full stop in", file_name
		return None
	
	return file_name[0:i]

def get_file_tag(file_name):
	"""Returns the file identifier associated with a path, ie for "/home/stevel/abc1234.mrc" would return abc1234
or for "bdb:hello99?1,2,3" would return hello99
	"""

	if file_name[:4].lower()=="bdb:" :
		dname=file_name.find("#")+1
		if dname==0 :dname=4
		dtail=file_name.find("?")
		if dtail>-1 : return file_name[dname:dtail]
		return file_name[dname:]
	
	dname=file_name.rfind("/")+1
	ddot=file_name.rfind(".")
	if ddot==-1 : return file_name[dname:]
	return file_name[dname:ddot]

def strip_after_dot(file_name):
	""" a function for stripping the contents of a filename so that all
	 that remains is up to the first '.'
	 eg if given image.sh4. mrc this functions strips the 'sh4.mrc' and returns 'image'	
	 FIXME it's probably easiest to do this with regular expressions... """
	idx = str.find(file_name,'.')
	return file_name[0:idx]


def get_platform():
	'''
	wraps platform.system but accommodates for its internal bad programming.
	Returns Darwin, Windows, Linux, or potentially something else
	'''
	import platform
	while True:
		try:
			return platform.system()
		except:
			pass
	
if get_platform() == "Darwin": 
	glut_inited = True # this is a hack for the time being

def remove_directories_from_name(file_name):
	'''
	Removes the directories from a file name.
	If the file_name is "/a/b/c.d", "c.d" is returned
	If the file_name is "/a/b/c/" (last character is '/'), "c" is returned
	If the file_name is "/a/b/c" , "e" is returned
	Works on Windows, Linux and Darwin)
	'''
	import platform
	pfm = get_platform() # will be Linux, Darwin or Windows, even Java
	if pfm == "Windows":
		idx = file_name.rfind('\\')
	else:
		idx = file_name.rfind('/')
		
	if idx == -1: return file_name
	elif idx == (len(file_name)-1): #If the file_name is "/a/b/c/" (last character is '/'), "c" is returned
		f = file_name[0:-1]
		return remove_directories_from_name(f)
	else: return file_name[idx+1:]


def name_has_no_tag(file_name):
	'''
	A convenient way of asking if the file name in has no tag. i.e.
	/home/tmp.jpg would have a tag but /home/tmp would not. Ofcourse
	this function will return true if the argument is the name of a
	folder, but that was not the original intended use
	'''
	idx1 = file_name.rfind("/")
	idx2 = file_name.rfind(".")
	
	if idx1 >= idx2: return True # -1 == -1 
	else: return False
	
# a function for testing whether a type of Averager, Aligner, Comparitor, Projector, Reconstructor etc
# can be created from the command line string. Returns false if there are problems
# examples
# if not check_eman2_type(options.simaligncmp,Cmps,"Comparitor") : exit(1)
# if not check_eman2_type(options.simalign,Aligners,"Aligner"): exit(1)
def check_eman2_type(modoptstring, object, objectname, verbose=True):
	if modoptstring == None:
		if verbose:
			print "Error: expecting a string but got python None, was looking for a type of %s" %objectname
		return False
	 
	if modoptstring == "":
		if verbose:
			print "Error: expecting a string was not empty, was looking for a type of %s" %objectname
		return False
	
	try:
		p = parsemodopt(modoptstring)
		if p[0] == None:
			if verbose:
				print "Error: Can't interpret the construction string %s" %(modoptstring)
			return False
		object.get(p[0], p[1])
	except RuntimeError:
		if (verbose):
			print "Error: the specified %s (%s) does not exist or cannot be constructed" %(objectname, modoptstring)
		return False

	return True


def qplot(img):
	"""This will plot a 1D image using qplot"""
	out=file("/tmp/plt.txt","w")
	for i in range(img.get_xsize()):
		out.write("%d\t%f\n"%(i,img.get_value_at(i,0)))
	out.close()
	os.system("qplot /tmp/plt.txt")

def error_exit(s) :
	"""A quick hack until I can figure out the logging stuff. This function
	should still remain as a shortcut"""
	print s
	exit(1)

def write_test_refine_data(num_im=1000):
	threed = test_image_3d()
	sym = Symmetries.get("c1")
	angles = sym.gen_orientations("rand",{"n":num_im})
	for angle in angles:
		image = threed.project("standard",angle)
		dx = Util.get_frand(-5,5)
		dy = Util.get_frand(-5,5)
		image.translate(dx,dy,0)
		image.process_inplace("math.addnoise",{"noise":1})
		image.write_image("bdb:starting_data#ptcls",-1)
	
	threed.write_image("bdb:refine_1#starting_model",-1)
	
def write_test_boxing_images(name="test_box",num_im=10,type=0,n=100):
	
	if type == 0:
		window_size=(128,128)
		image_size=(4096,4096)
	elif type == 1:
		window_size=(128,128)
		image_size=(4482,6678)
	elif type == 2:
		window_size=(128,128)
		image_size=(8964,13356)
	
	for i in range(num_im):
		im = test_boxing_image(window_size,image_size,n)
		im.write_image(name+"_"+str(i)+".mrc",0,EMUtil.ImageType.IMAGE_UNKNOWN, False,None,EMUtil.EMDataType.EM_SHORT)

def test_boxing_image(window_size=(128,128),image_size=(4096,4096),n=100):
	'''
	Returns an image useful for testing boxing procedures
	A randomly oriented and randomly flipped scurve test image is inserted into a larger image n times.
	The large image has gaussian noise added to it. Function arguments give control of the window size
	(of the scurve image), the size of the large returned image, and the number of inserted scurve images.
	'''
	ret = EMData(*image_size)
	
	x_limit = window_size[0]
	y_limit = window_size[0]
	scurve = test_image(0,window_size)
	for i in range(n):
		window = scurve.copy()
		da = Util.get_frand(0,360)
		flip = Util.get_irand(0,1)
		
		t = Transform({"type":"2d","alpha":da})
		t.set_mirror(flip)
		window.transform(t)
		#if flip:
			#window.process_inplace("xform.flip",{"axis":"x"})
		
		p = (Util.get_irand(x_limit,image_size[0]-x_limit),Util.get_irand(y_limit,image_size[1]-y_limit))
		
		ret.insert_clip(window,p)
		
	
	noise = EMData(*image_size)
	noise.process_inplace("testimage.noise.gauss")
	ret.add(noise)
	
	return ret

def test_image_array(subim,size=(0,0),n_array=(1,1)):
	"""This will build a packed array of 2-D images (subim) into a new
image of the specified size. The number of subimages in X and y can be 
independently defined. This is useful for making simulated 2-D crystals
(with an orthogonal geometry). Size will default to just fit the specified
number of subimages"""
	if size==(0,0): size=(subim.get_xsize()*n_array[0],subim.get_ysize()*n_array[1])

	out=EMData(*size)
	
	for x in range(n_array[0]):
		for y in range(n_array[1]):
			out.insert_clip(subim,(size[0]/2+int((x-n_array[0]/2.0)*subim.get_xsize()),size[1]/2+int((y-n_array[1]/2.0)*subim.get_ysize())))

	return out
	
def test_image(type=0,size=(128,128)):
	"""Returns a simple standard test image
	type=0  scurve
	type=1	gaussian noise, 0 mean, sigma 1
	type=2  square
	type=3  hollow square
	type=4  circular sinewave
	type=5  axes
	type=6  linewave
	type=7  scurve pluse x,y gradient
	type=8  scurve translated
	type=9  scurve with gaussian noise(mean 0, sigma 1)
	size=(128,128) """
	ret=EMData()
	ret.set_size(*size)
	if type==0 :
		ret.process_inplace("testimage.scurve")
	elif type==1 :
		ret.process_inplace("testimage.noise.gauss")
	elif type==2:
		ret.process_inplace("testimage.squarecube",{"edge_length":size[0]/2})
	elif type==3:
		ret.process_inplace("testimage.squarecube",{"fill":1,"edge_length":size[0]/2})
	elif type==4:
		ret.process_inplace("testimage.scurve")
		t = EMData()
		t.set_size(*size)
		t.process_inplace("testimage.linewave",{"period":Util.get_irand(43,143)})
		ret.add(t)
	elif type==5:
		ret.process_inplace("testimage.axes")
	elif type==6:
		ret.process_inplace("testimage.linewave",{"period":Util.get_irand(43,143)})
	elif type==7:
		ret.process_inplace("testimage.scurve")
		ret.mult(10)
		tmp = EMData(*size)
		tmp.process_inplace("testimage.gradient")
		ret.add(tmp)
		tmp.process_inplace("testimage.gradient",{"axis":"y"})
		ret.add(tmp)
		ret.process_inplace("normalize.edgemean")
	elif type==8:
		ret.process_inplace("testimage.scurve")
		t = Transform({"type":"2d","alpha":Util.get_frand(0,360)})
		t.set_trans(int(size[0]/10),int(size[1]/10),0)
		t.set_mirror(Util.get_irand(0,1))
		ret.transform(t)
	elif type==9:
		ret.process_inplace("testimage.scurve")
		tmp = EMData(*size)
		tmp.process_inplace("testimage.noise.gauss")
		ret.add(tmp)
	else:
		raise	
	
	
	return ret
	
def test_image_3d(type=0,size=(128,128,128)):
	"""Returns a simple standard test image
	type=0  axes
	type=1	gaussian noise, 0 mean, sigma 1
	type=2  gradient
	type=3  square
	type=4  sphere
	size=(128,128,128) """
	ret=EMData()
	if len(size) != 3:
		print "error, you can't create a 3d test image if there are not 3 dimensions in the size parameter"
		return None
	if type != 2: ret.set_size(*size)
	else: ret.set_size(256,256,64)
	if type==0 :
		ret.process_inplace("testimage.axes")
	elif type==1:
		tmp = EMData()
		tmp.set_size(*size)
		tmp.process_inplace("testimage.sphericalwave",{"wavelength":size[0]/7.0,"phase":0})
		
		a = tmp.copy()
		a.translate(size[0]/7.0,size[1]/7.0,0)
		ret.process_inplace("testimage.sphericalwave",{"wavelength":size[0]/11.0,"phase":0})
		ret.add(a)
		
		a = tmp.copy()
		a.translate(-size[0]/7.0,size[1]/7.0,0)
		ret.add(a)
		
		a = tmp.copy()
		a.translate(-size[0]/7.0,-size[1]/7.0,0)
		ret.add(a)
		
		a = tmp.copy()
		a.translate(size[0]/7.0,-size[1]/7.0,0)
		ret.add(a)
		
		ret.process_inplace("normalize")
		
	elif type==2:		
		ret.process_inplace("testimage.tomo.objects")
	elif type==3:
		ret.process_inplace("testimage.squarecube",{"fill":1,"edge_length":size[0]/2})
	elif type==4:
		ret.process_inplace("testimage.circlesphere",{"radius":int(size[0]*.375)})
	elif type==5:
		
		t = Transform({"type":"eman","az":60,"alt":30})
		ret.process_inplace("testimage.ellipsoid",{"a":size[0]/3,"b":size[1]/5,"c":size[2]/4,"transform":t})
		
		t = Transform({"type":"eman","az":-45})
		t.set_trans(0,0,0)
		ret.process_inplace("testimage.ellipsoid",{"a":size[0]/2,"b":size[1]/16,"c":size[2]/16,"transform":t,"fill":0})
		
		t.set_trans(0,0,size[2]/6)
		ret.process_inplace("testimage.ellipsoid",{"a":size[0]/2,"b":size[1]/16,"c":size[2]/16,"transform":t,"fill":0})
		
		t.set_trans(0,0,-size[2]/6)
		ret.process_inplace("testimage.ellipsoid",{"a":size[0]/2,"b":size[1]/16,"c":size[2]/16,"transform":t,"fill":0})
		
		t = Transform({"type":"eman","alt":-45})
		t.set_trans(-size[0]/8,size[1]/4,0)
		ret.process_inplace("testimage.ellipsoid",{"a":size[0]/16,"b":size[1]/2,"c":size[2]/16,"transform":t,"fill":0})
		
		t = Transform({"type":"eman","alt":-45})
		t.set_trans(size[0]/8,-size[1]/3.5)
		ret.process_inplace("testimage.ellipsoid",{"a":size[0]/16,"b":size[1]/2,"c":size[2]/16,"transform":t,"fill":0})
		
	elif type==6 :
		ret.process_inplace("testimage.noise.gauss")
		
	return ret

# get a font renderer
def get_3d_font_renderer():
	font_renderer = EMFTGL()
	font_renderer.set_face_size(32)
	font_renderer.set_using_display_lists(True)
	font_renderer.set_depth(2)
	pfm = get_platform()
	if pfm in ["Linux","Darwin"]:
				font_renderer.set_font_file_name(os.getenv("EMAN2DIR")+"/fonts/DejaVuSerif.ttf")
	elif pfm == "Windows":
			font_renderer.set_font_file_name("C:\\WINDOWS\\Fonts\\arial.ttf")
	else:
			print "unknown platform:",pfm
	return font_renderer

class EMAbstractFactory:
	''' 
	see http://blake.bcm.edu/emanwiki/Eman2FactoriesInPython
	'''
	
	def register(self, methodName, constructor, *args, **kargs):
		"""register a constructor"""
		_args = [constructor]
		_args.extend(args)
#		setattr(self, methodName,Functor(_args, kargs))
 		setattr(self, methodName, EMFunctor(*_args, **kargs))
		
	def unregister(self, methodName):
		"""unregister a constructor"""
		delattr(self, methodName)
		
class EMFunctor:
	''' 
	Taken from http://code.activestate.com/recipes/86900/
	'''	  
	def __init__(self, function, *args, **kargs):
		assert callable(function), "function should be a callable obj"
		self._function = function
		self._args = args
		self._kargs = kargs
		
	def __call__(self, *args, **kargs):
		"""call function"""
		_args = list(self._args)
		_args.extend(args)
		_kargs = self._kargs.copy()
		_kargs.update(kargs)
		return self._function(*_args, **_kargs)

def isosurface(marchingcubes, threshhold, smooth=False):
	"""Return the Isosurface points, triangles, normals(smooth=True), normalsSm(smooth=False)"""
	marchingcubes.set_surface_value(threshhold)
	d = marchingcubes.get_isosurface(smooth)
	return d['points'], d['faces'], d['normals']

# determines if all of the data dimensions are a power of val
# e.g. if ( data_dims_power_of(emdata,2) print "the dimensions of the image are all a power of 2"
def data_dims_power_of(data,val):
	
	test_cases = [data.get_xsize()]
	
	if ( data.get_ndim() >= 2 ):
		test_cases.append(data.get_ysize())
	if ( data.get_ndim == 3):
		test_cases.append(data.get_zsize())

	for i in test_cases:
		x = i
		while ( x > 1 and x % val == 0 ): x /= val
		if x != 1: 
			return False
		
	return True

__doc__ = \
"EMAN classes and routines for image/volume processing in \n\
single particle reconstructions.\n\
\n\
The following classes are defined: \n\
  EMData - the primary class to process electronic microscopy images. \n\
 \n\
  Quaternion - implements mathematical quaternion. \n\
  Region - defines a rectangular 2D/3D region. \n\
  Transform3D - defines a transformation including rotation, translation, and different Euler angles. \n\
  Vec3i - a 3-element integer vector. \n\
  Vec3f - a 3-element floating number vector. \n\
\n\
  EMObject - A wrapper class for int, float, double, string, EMData, XYData, list etc. \n\
  Pixel - defines a pixel's 3D coordinates and its value. \n\
  SimpleCtf - defines EMAN CTF parameter model. \n\
  XYData - implements operations on a series of (x y) data pair. \n\
\n\
  Aligners - Aligner factory. Each Aligner alignes 2D/3D images. \n\
  Averagers - Averager factory. Each Averager averages a set of images. \n\
  Cmps  - Cmp factory. Each Cmp defines a way to do image comparison. \n\
  Processors - Processor factory. Each processor implements an image-processing algorithm. \n\
  Projectors - Projector factory. Each Projector implements an algorithm for 3D image projection. \n\
  Reconstructors - Reconstructor factory. Each Reconstructor implements an algorithm for image reconstruction. \n\
\n\
  EMUtil - Defines utility functions for EMData-related operations. \n\
  TestUtil - Unit test utility functions. \n\
  Util - Generic utility functions. \n\
\n\
  EMNumPy - Defines functions for conversions between EMData and numpy array. \n\
  Log - Log output at different verbose level. \n\
  PointArray - Point array. \n\
\n\
  dump_aligners() - Print out all Aligners and their parameters. \n\
  dump_averagers() - Print out all Averagers and their sparameters. \n\
  dump_cmps() - Print out all Cmps and their parameters. \n\
  dump_processors() - Print out all Processor`s and their parameters. \n\
  dump_projectors() - Print out all Projectors and their parameters. \n\
  dump_reconstructors() - Print out all Reconstructors and their parameters. \n\
  dump_analyzers() - Print out all Analyzers anf their parameters. \n\
"
