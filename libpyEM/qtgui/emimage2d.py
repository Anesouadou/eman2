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

import PyQt4
from PyQt4 import QtCore, QtGui, QtOpenGL
from PyQt4.QtCore import Qt
from OpenGL import GL,GLU,GLUT
from OpenGL.GL import *
from valslider import ValSlider
from math import *
from EMAN2 import *
import EMAN2
import sys
import numpy
import struct
from emimageutil import ImgHistogram,EMEventRerouter, EMParentWin
import emshape 
from emshape import EMShape
from weakref import WeakKeyDictionary
from pickle import dumps,loads

from emglobjects import EMOpenGLFlagsAndTools, EMGUIModule
from emapplication import EMStandAloneApplication, EMGUIModule

from emanimationutil import SingleValueIncrementAnimation,Animator, LineAnimation

try: from PyQt4 import QtWebKit
except: pass
import platform

MAG_INC = 1.1

from emglobjects import EMOpenGLFlagsAndTools

GLUT.glutInit(sys.argv)

class EMImage2DWidget(QtOpenGL.QGLWidget,EMEventRerouter,Animator):
	allim=WeakKeyDictionary()
	def __init__(self, em_image_2d_module,enable_timer=True):
		Animator.__init__(self)
		fmt=QtOpenGL.QGLFormat()
		fmt.setDoubleBuffer(True)
		#fmt.setSampleBuffers(True)
		fmt.setDepth(1)
		QtOpenGL.QGLWidget.__init__(self,fmt)
		EMEventRerouter.__init__(self,em_image_2d_module) # makes self.target
		self.initimageflag = True
		
		self.setFocusPolicy(Qt.StrongFocus)
		
		self.time_enabled = False
		if enable_timer:
			self.enable_timer()
		
		self.resize(480,480)
		
	def enable_timer(self):
		if self.time_enabled == False:
			self.timer = QtCore.QTimer()
			QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.time_out)
			self.timeinterval = 50
			self.timer.start(50)
			self.time_enabled = True
		else: print "timer already enabled in emimage2d"
		
	def set_parent(self,parent):
		self.parent = parent

	def set_data(self,data):
		self.target.set_data(data)
		
	def initializeGL(self):
		GL.glClearColor(0,0,0,0)
		
		glLightfv(GL_LIGHT0, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
		glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
		glLightfv(GL_LIGHT0, GL_POSITION,  [.1,.1,1,0.])
	
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		try:
			self.target.initializeGL()
			self.initimageflag = False
		except:
			pass
	
	def paintGL(self):
		if not self.target: return
		
		glClear(GL_COLOR_BUFFER_BIT)
		if glIsEnabled(GL_DEPTH_TEST):
			glClear(GL_DEPTH_BUFFER_BIT)
		if glIsEnabled(GL_STENCIL_TEST):
			glClear(GL_STENCIL_BUFFER_BIT)

		
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		
		#self.cam.position()
		if self.initimageflag == True:
			self.target.initializeGL()
			self.initimageflag = False
		#context = OpenGL.contextdata.getContext(None)
		#print "Image2D context is", context
		glPushMatrix()
		self.target.render()
		glPopMatrix()
		
	def resizeGL(self, width, height):
		side = min(width, height)
		
		GL.glViewport(0,0,width,height)
	
		GL.glMatrixMode(GL.GL_PROJECTION)
		GL.glLoadIdentity()
		GLU.gluOrtho2D(0.0,width,0.0,height)
		GL.glMatrixMode(GL.GL_MODELVIEW)
		GL.glLoadIdentity()
		
		try: self.target.resizeEvent(width,height)
		except: pass
		
	def add_shapes(self,s):
		self.target.add_shapes(s)
		
	def add_shape(self,name,shape):
		return self.target.add_shape(name,shape)

	def scr_to_img(self,p):
		return self.target.scr_to_img(p)
	
	def set_active(self,a,b,c,d):
		return self.target.set_active(a,b,c,d)
	
	def get_shapes(self):
		return self.target.get_shapes()
	
	def del_shapes(self):
		return self.target.del_shapes()
	
	def del_shape(self,p):
		return self.target.del_shape(p)

	def scroll_to(self,x,y):
		return self.target.scroll_to(x,y)
	
	def register_scroll_motion(self,x,y):
		return self.target.register_scroll_motion(x,y)
	
	def get_depth_for_height(self, height):
		return 0
	
	def get_shapes(self):
		return self.target.get_shapes()

class EMImage2DMouseEvents:
	'''
	A base class for objects that handle mouse events in the EMImageMXModule
	'''
	def __init__(self,mediator):
		'''
		Stores only a reference to the mediator
		'''
		if not isinstance(mediator,EMImage2DMouseEventsMediator):
			print "error, the mediator should be a EMMXCoreMouseEventsMediator"
			return
		self.mediator = mediator
	def mouse_up(self,event): pass
	def mouse_down(self,event): pass
	def mouse_drag(self,event):	pass
	def mouse_move(self,event): pass
	def mouse_wheel(self,event):pass


class EMImage2DMouseEventsMediator:
	def __init__(self,target):
		if not isinstance(target,EMImage2DModule):
			print "error, the target should be a EMImage2DModule"
			return
		
		self.target = target
	
	def get_parent(self):
		return self.target.get_parent()
	
	def emit(self,*args,**kargs):
		self.target.emit(*args,**kargs)
		
	def get_inspector(self):
		return self.target.get_inspector()
	
	def add_shape(self,shape_string,shape):
		self.target.add_shape(shape_string,shape)
		
	def del_shape(self,shape_string):
		self.target.del_shape(shape_string)
		
	def get_shapes(self):
		return self.target.get_shapes()

	def scr_to_img(self,x,y):
		return self.target.scr_to_img(x,y)
	
	def force_display_update(self):
		self.target.force_display_update()
		
	def get_data(self):
		return self.target.get_data()
	
	def set_data(self,data):
		self.target.set_data(data)
		
	def replace_data(self,data):
		self.target.replace_data(data)
		
	def updateGL(self):
		self.target.updateGL()
		
	def redo_fft(self):
		self.target.redo_fft()

class EMImage2DEmitMouseMode(EMImage2DMouseEvents):
	def __init__(self,mediator):
		EMImage2DMouseEvents.__init__(self,mediator)
		
	def mouse_up(self,event):
		lc=self.mediator.scr_to_img(event.x(),event.y())
		self.mediator.emit(QtCore.SIGNAL("mouseup"), event,lc)

	def mouse_down(self,event):
		lc=self.mediator.scr_to_img(event.x(),event.y())
		self.mediator.emit(QtCore.SIGNAL("mousedown"), event,lc)
		
	def mouse_move(self,event):
		lc=self.mediator.scr_to_img(event.x(),event.y())
		if event.buttons()&Qt.LeftButton:
			self.mediator.emit(QtCore.SIGNAL("mousedrag"), event,lc)
		else:
			self.mediator.emit(QtCore.SIGNAL("mousemove"), event,lc)
		
	def mouse_wheel(self,event):
		self.mediator.emit(QtCore.SIGNAL("mousewheel"), event)

class EMImage2DMeasureMode(EMImage2DMouseEvents):
	def __init__(self,mediator):
		EMImage2DMouseEvents.__init__(self,mediator)
		
	def mouse_up(self,event):
		if event.buttons()&Qt.LeftButton:
			self.mediator.add_shape("MEAS",EMShape(("line",.5,.1,.5,current_shapes["MEAS"].shape[4],current_shapes["MEAS"].shape[5],lc[0],lc[1],2)))
			
	def mouse_down(self,event):
		if event.buttons()&Qt.LeftButton:
			lc=self.mediator.scr_to_img(event.x(),event.y())
			self.mediator.del_shape("MEASL")
			self.mediator.del_shape("MEAS")
			self.mediator.add_shape("MEAS",EMShape(("line",.5,.1,.5,lc[0],lc[1],lc[0]+1,lc[1],2)))
			self.mediator.updateGL()
			
	def mouse_move(self,event):
		if event.buttons()&Qt.LeftButton:
			lc=self.mediator.scr_to_img(event.x(),event.y())
			current_shapes = self.mediator.get_shapes()
			self.mediator.add_shape("MEAS",EMShape(("line",.5,.1,.5,current_shapes["MEAS"].shape[4],current_shapes["MEAS"].shape[5],lc[0],lc[1],2)))
			
			dx=lc[0]-current_shapes["MEAS"].shape[4]
			dy=lc[1]-current_shapes["MEAS"].shape[5]
			self.mediator.add_shape("MEASL",EMShape(("label",.1,.1,.1,lc[0]+2,lc[1]+2,"%d,%d - %d,%d"%(current_shapes["MEAS"].shape[4],current_shapes["MEAS"].shape[5],lc[0],lc[1]),9,-1)))
			
			inspector = self.mediator.get_inspector()
			if inspector:
				apix=inspector.mtapix.value
				inspector.mtshoworigin.setText("Start: %d , %d"%(current_shapes["MEAS"].shape[4],current_shapes["MEAS"].shape[5]))
				inspector.mtshowend.setText("  End: %d , %d"%(lc[0],lc[1]))
				inspector.mtshowlen.setText("dx,dy (len): %1.2f , %1.2f (%1.3f)"%(dx*apix,dy*apix,hypot(dx,dy)*apix))
				
			self.mediator.updateGL()
		
	def mouse_wheel(self,event):
		pass

class EMImage2DDrawMouseMode(EMImage2DMouseEvents):
	def __init__(self,mediator):
		EMImage2DMouseEvents.__init__(self,mediator)
		self.drawr1=-1
		self.drawv1=-1
		self.drawr2=-1
		self.drawv2=-1
		
	def mouse_up(self,event):
		if event.button()==Qt.LeftButton:
			self.mediator.redo_fft()
			self.mediator.force_display_update()
			self.mediator.updateGL()
			
	def mouse_down(self,event):
		if event.buttons()&Qt.LeftButton:
			inspector = self.mediator.get_inspector()
			lc=self.mediator.scr_to_img(event.x(),event.y())
			if inspector:
				self.drawr1=int(float(inspector.dtpen.text()))
				self.drawv1=float(inspector.dtpenv.text())
				self.drawr2=int(float(inspector.dtpen2.text()))
				self.drawv2=float(inspector.dtpenv2.text())
				self.mediator.get_data().process_inplace("mask.paint",{"x":lc[0],"y":lc[1],"z":0,"r1":self.drawr1,"v1":self.drawv1,"r2":self.drawr2,"v2":self.drawv2})
				self.mediator.force_display_update()
				self.mediator.updateGL()
					
	def mouse_move(self,event):
		if event.buttons()&Qt.LeftButton:
			lc=self.mediator.scr_to_img(event.x(),event.y())
			self.mediator.get_data().process_inplace("mask.paint",{"x":lc[0],"y":lc[1],"z":0,"r1":self.drawr1,"v1":self.drawv1,"r2":self.drawr2,"v2":self.drawv2})
			self.mediator.force_display_update()
			self.mediator.updateGL()
			
	def mouse_wheel(self,event):
		pass


class EMImage2DModule(EMGUIModule):
	"""
	"""
	allim=WeakKeyDictionary()
	
	def emit(self,*args,**kargs):
		qt_widget = self.application.get_qt_emitter(self)
		qt_widget.emit(*args,**kargs)
	
	def get_qt_widget(self):
		if self.parent == None:	
			self.gl_parent = EMImage2DWidget(self,enable_timer=True)
			self.parent = EMParentWin(self.gl_parent)
			self.gl_widget = self.gl_parent
			self.set_gl_parent(self.gl_parent)
			f = self.file_name.split('/')
			f = f[len(f)-1]
			self.parent.setWindowTitle(f)
			if isinstance(self.data,EMData):
				self.load_default_scale_origin()
		return self.parent
	
	def get_gl_widget(self,qt_parent=None):
		from emfloatingwidgets import EMGLView2D_v2, EM2DGLWindow
		self.init_size_flag = False
		if self.gl_widget == None:
			gl_view = EMGLView2D_v2(self,image=None)
			self.gl_widget = EM2DGLWindow(self,gl_view)
			self.set_gl_parent(qt_parent)
			self.gl_widget.target_translations_allowed(True)
		return self.gl_widget
		
	def get_desktop_hint(self):
		return "image"
	
	def __parent_resize(self):
		#if self.gl_widget != None: return
		self.load_default_scale_origin()
		
#		print "resizing"
#		try:
#			parent = self.get_parent()
#			if self.parent_geometry != None:
#				parent.restoreGeometry(self.parent_geometry)
#			elif self.data.get_xsize()<1024 and self.data.get_ysize()<1024: 
#				parent.resize(self.data.get_xsize(),self.data.get_ysize())
#				self.load_default_scale_origin()
#			else:
#				parent.resize(800,800)
#				self.load_default_scale_origin()
#			self.init_size_flag = False
#		except: pass
			
	
	def __init__(self, image=None,application=None):
		self.data = image 	   # EMData object to display
		self.file_name = ""# stores the filename of the image, if None then member functions should be smart enough to handle it
		EMGUIModule.__init__(self,application,ensure_gl_context=True)
		
		self.init_gl_flag = True
		self.oldsize=(-1,-1)
		self.scale=1.0				# Scale factor for display
		self.origin=(0,0)			# Current display origin
		self.invert=0				# invert image on display
		self.gamma=1.0				# gamma for display (impact on inverted contrast ?
		self.minden=0
		self.maxden=1.0
		self.fgamma = 1.0
		self.fminden=0
		self.fmaxden=1.0
		self.display_fft = None		# a cached version of the FFT
		self.fft=None				# The FFT of the current target if currently displayed
		self.rmousedrag=None		# coordinates during a right-drag operation
		self.mmode=0				# current mouse mode as selected by the inspector
		self.curfft=0				# current FFT mode (when starting with real images only)
		self.mag = 1.1				# magnification factor
		self.invmag = 1.0/self.mag	# inverse magnification factor
		
		self.shapes={}				# dictionary of shapes to draw, see add_shapes
		self.shapechange=1			# Set to 1 when shapes need to be redrawn
		self.active=(None,0,0,0)	# The active shape and a hilight color (n,r,g,b)
		
		self.extras = []			# an empty set of extras - other images that can be rendered over this one
		
		self.startorigin = None
		self.endorigin = None
		self.isanimated = False
		self.time = 1
		self.timeinc = 0.125
		
		self.init_size = True		# A flag used to set the initial origin offset
		
		self.shapelist = 0			# a display list identify
		
		self.glflags = EMOpenGLFlagsAndTools() 	# supplies power of two texturing flags
		
		self.suppress_inspector = False 	# Suppresses showing the inspector - switched on in emfloatingwidgets
		self.tex_name = 0			# an OpenGL texture handle
		
		self.otherdata = None
		self.otherdatascale = -1
		self.otherdatablend = False
		self.other_tex_name = None
		self.init_size_flag = True
		self.frozen = False
		self.isexcluded = False
		self.hack_shrink = 1
		self.parent_geometry = None
		self.font_renderer = None
		
		self.list_data = None 			# this can be used for viewing lists of data
		self.list_fft_data = None		# this is used for doing the ffts of list data
		self.list_idx = 0	# and idx to the list_data
		
		self.use_display_list = True # whether or not a display list should be used to render the image pixelsw - if on, this will save on time if the view of the image is unchanged, which can quite often be the case
		self.main_display_list = 0	# if using display lists, the stores the display list
		self.display_states = [] # if using display lists, this stores the states that are checked, and if different, will cause regeneration of the display list
		self.hist = []
		
		self.wheel_navigate = False # useful on Mac laptops
		
		try: self.parent.setAcceptDrops(True)
		except:	pass
		
		if image : self.set_data(image)
		else:self.__load_display_settings_from_db()
		
		self.__init_mouse_handlers()
		
	def __init_mouse_handlers(self):
		self.mouse_events_mediator = EMImage2DMouseEventsMediator(self)
		self.mouse_event_handlers = {}
		self.mouse_event_handlers["emit"] = EMImage2DEmitMouseMode(self.mouse_events_mediator)
		self.mouse_event_handlers["measure"] = EMImage2DMeasureMode(self.mouse_events_mediator)
		self.mouse_event_handlers["draw"] = EMImage2DDrawMouseMode(self.mouse_events_mediator)
		self.mouse_event_handler = self.mouse_event_handlers["emit"]
		
	def __del__(self):
		if (self.shapelist != 0):
			glDeleteLists(self.shapelist,1)
			self.shapelist = 0
		if self.main_display_list != 0:
			glDeleteLists(self.main_display_list,1)
			self.main_display_list = 0
	
	def set_mouse_mode(self,mode):
		self.mmode = mode
		if mode == 0:
			self.mouse_event_handler = self.mouse_event_handlers["emit"]
		elif mode == 1:
			self.mouse_event_handler = self.mouse_event_handlers["measure"]
		elif mode == 2:
			self.mouse_event_handler = self.mouse_event_handlers["draw"]
		else:
			print "unknown mouse mode:",mode
			return
		
	def get_minden(self): return self.minden
	def get_maxden(self): return self.maxden
	def get_gamma(self): return self.gamma
	def get_shapes(self): return self.shapes
	
	def set_density_range(self,x0,x1):
		"""Set the range of densities to be mapped to the 0-255 pixel value range"""
		if self.curfft == 0:
			self.minden=x0
			self.maxden=x1
		else:
			self.fminden=x0
			self.fmaxden=x1
		self.force_display_update()
		self.updateGL()
	
	def set_density_min(self,val):
		if self.curfft == 0:
			self.minden=val
		else:
			self.fminden=val
		self.force_display_update()
		self.updateGL()
		
	def set_density_max(self,val):
		if self.curfft == 0:
			self.maxden=val
		else:
			self.fmaxden=val
		self.force_display_update()
		self.updateGL()
	
	def set_gamma(self,val):
		if self.curfft == 0:
			self.gamma=val
		else:
			self.fgamma=val
		self.force_display_update()
		self.updateGL()
	
	def set_file_name(self,file_name,load_cache_settings=True):
		self.file_name = file_name
		try:
			f = self.file_name.split('/')
			f = f[len(f)-1]
			self.get_parent().setWindowTitle(f)
		except:pass
		
		if load_cache_settings:
			self.__load_display_settings_from_db()
		
	def get_file_name(self):
		return self.file_name
	
	def set_other_data(self,data,scale,blend=False):
		self.otherdata = data
		self.otherdatascale = scale
		self.otherdatablend = blend
	
	def get_data_dims(self):
		data = None
		
		if self.data != None: data = self.data
		elif self.fft != None: data = self.fft
		else: return [0,0,0]
			
		return [data.get_xsize(),data.get_ysize(),data.get_zsize()]
	
	def width(self):
		try: return self.gl_widget.width()
		except:	return 0
	
	def height(self):
		try: return self.gl_widget.height()
		except:	return 0
	
	def updateGL(self):
		try: self.gl_widget.updateGL()
		except: pass
		
	def set_frozen(self,frozen):
		self.frozen = frozen
		
	def set_excluded(self,isexcluded):
		wasexcluded = self.isexcluded
		
		self.isexcluded = isexcluded
		
		if wasexcluded or self.isexcluded: return True
		else: return False
	
	def get_data(self):
		return self.data
	
	
	def set_data(self,data,file_name=""):
		"""You may pass a single 2D image or a list of images"""
		if self.data != None and self.file_name != "":
			self.__write_display_settings_to_db()
			
		self.set_file_name(file_name,load_cache_settings=False)
	
		fourier = False
		if isinstance(data,list):
			self.list_idx = len(data)/2
			d = data[0]
			if d.is_complex():
				self.list_data = []
				self.list_fft_data = data
				for i in range(len(data)):self.list_data.append(None)
				self.curfft = 2
				self.__set_display_image(self.curfft)
				fourier = True
			else:
				self.list_data = data
				self.data = self.list_data[self.list_idx]
				self.list_fft_data = []
				for i in range(len(data)):self.list_fft_data.append(None)
				
			self.get_inspector().enable_image_range(1,len(data),self.list_idx+1)
		else:
			self.get_inspector().disable_image_range()
			self.list_data = None
			self.list_fft_data = None
			if data.is_complex():
				fourier = True
				self.fft = data.copy()# have to make copies here because we alter it!
				self.fft.set_value_at(0,0,0,0) # get rid of the DC component
				self.fft.set_value_at(1,0,0,0) # this should already by 0... ?
				self.curfft = 2
				self.__set_display_image(self.curfft)
				inspector = self.get_inspector()
				inspector.set_fft_amp_pressed()
				fourier = True
			else: self.data = data
	
		#fourier = False
		#d = data
		#if isinstance(d,list): d = d[0]
		#if d.is_complex():
			#fourier = True
			#self.fft = data.copy()# have to make copies here because we alter it!
			#self.fft.set_value_at(0,0,0,0) # get rid of the DC component
			#self.fft.set_value_at(1,0,0,0) # this should already by 0... ?
			#self.curfft = 2
			#self.__set_display_image(self.curfft)
			#inspector = self.get_inspector()
			#inspector.set_fft_amp_pressed()
		#else:
			#self.data=data
			
			#if isinstance(data,list):
				#self.list_data = data
				#self.list_idx = len(self.list_data)/2
				#self.data = data[self.list_idx]
			#else:
				#self.list_data = None
			
		self.auto_contrast(inspector_update=False,display_update=False)

		self.load_default_scale_origin()
		
		self.__load_display_settings_from_db(inspector_update=False,display_update=False)
		
		self.inspector_update(use_fourier=fourier)
		self.force_display_update()
		
	def load_default_scale_origin(self):
		self.scale=1.0				# Scale factor for display
		self.origin=(0,0)
		try: 
			w = self.gl_widget.width()
			h = self.gl_widget.height()
			data = self.get_data_dims()
			if data[0] == 0 or data[1] == 0: raise
			scalew = float(w)/data[0]
			scaleh = float(h)/data[1]
			if scaleh < scalew:
				self.scale = scaleh
			else: self.scale = scalew
		except: pass
	
	def auto_contrast(self,bool=False,inspector_update=True,display_update=True):
		if self.curfft == 0:
			if self.data == None: return
			mean=self.data.get_attr("mean")
			sigma=self.data.get_attr("sigma")
			m0=self.data.get_attr("minimum")
			m1=self.data.get_attr("maximum")
			self.minden=max(m0,mean-3.0*sigma)
			self.maxden=min(m1,mean+3.0*sigma)
			if inspector_update: self.inspector_update()
			if display_update: self.force_display_update()
		else:
			if self.display_fft == None: return
			
			mean=self.display_fft.get_attr("mean")
			sigma=self.display_fft.get_attr("sigma")
			m0=self.display_fft.get_attr("minimum")
			m1=self.display_fft.get_attr("maximum")
		
			self.fminden=0
			self.fmaxden=min(m1,mean+5.0*sigma)
			
			self.force_display_update()
			
			if inspector_update: self.inspector_update(use_fourier=True)
			if display_update: self.updateGL()

	def __load_display_settings_from_db(self,inspector_update=True,display_update=True):
		if self.file_name == "": return # there is no file name, we have no means to stores information
		
		try:
			DB = EMAN2db.EMAN2DB.open_db(".")
			DB.open_dict("image_2d_display_settings")
		except:
			# Databasing is not supported, in which case w
			print "no db support - remove the database directory in /tmp"
			return
		
		db = DB.image_2d_display_settings
	
		data = db[self.file_name]
		if data == None: return
		try:
			self.minden = data["min"]
			self.maxden = data["max"]
			self.fminden = data["fourier_min"]
			self.fmaxden = data["fourier_max"]
			self.fgamma = data["fourier_gamma"]
			self.gamma = data["gamma"]
			self.scale = data["scale"] 
			self.origin = data["origin"]
		except: pass
		try:
			self.parent_geometry = data["parent_geometry"]
			if self.parent != None:
				try:
					self.parent.restoreGeometry(self.parent_geometry)
				except: pass
		except:pass
		
		if inspector_update: self.inspector_update()
		if display_update: self.force_display_update()
	
	def __write_display_settings_to_db(self):
		'''
		writes the min,max, brightness, contrast and gamma values associated with
		the current image to the homedb. The full path of the image is used
		'''
		
		if self.file_name == None: return # there is no file name, we have no means to stores information
		
		try:
			DB = EMAN2db.EMAN2DB.open_db(".")
			DB.open_dict("image_2d_display_settings")
		except:
			# Databasing is not supported, in which case we do nothing
			return
		
		data = {}	
		data["min"] = self.minden
		data["max"] = self.maxden
		data["fourier_min"] = self.fminden
		data["fourier_max"] = self.fmaxden
		data["fourier_gamma"] = self.fgamma
		data["gamma"] = self.gamma
		data["origin"] = self.origin
		data["scale"] = self.scale
		
		try:
			data["parent_geometry"] = self.parent.saveGeometry()
		except: pass
		
		db = DB.image_2d_display_settings
		db[self.file_name] = data

	def set_origin(self,x,y):
		"""Set the display origin within the image"""
		self.origin=(x,y)
		self.updateGL()
	
	def scroll_to(self,x,y):
		"""center the point on the screen"""
		self.set_origin(x*self.scale-self.gl_widget.width()/2,y*self.scale-self.gl_widget.height()/2)

	def set_shapes(self,shapes,shrink):
		self.hack_shrink = shrink
		self.shapes = shapes
		self.shapechange=1
		
	def register_scroll_motion(self,x,y):
		animation = LineAnimation(self,self.origin,(x*self.scale-self.gl_widget.width()/2,y*self.scale-self.gl_widget.height()/2))
		self.get_gl_parent().register_animatable(animation)
		return True

	def set_scale(self,newscale):
		"""Adjusts the scale of the display. Tries to maintain the center of the image at the center"""
		try:
			self.origin=(newscale/self.scale*(self.gl_widget.width()/2.0+self.origin[0])-self.gl_widget.width()/2.0,newscale/self.scale*(self.gl_widget.height()/2.0+self.origin[1])-self.gl_widget.height()/2.0)
			self.scale=newscale
			self.updateGL()
		except: pass
		
	def set_invert(self,val):
		if val: self.invert=1
		else : self.invert=0
		self.updateGL()
		
	def set_FFT(self,val):
		if self.data != None and self.data.is_complex():
			print " I am returning"
			return

		self.curfft=val
		
		fourier = self.__set_display_image(val)

		self.inspector_update(use_fourier=fourier)
	
		self.force_display_update()
		self.updateGL()

	def redo_fft(self):
		if self.list_data == None:
			self.fft = None
		else:
			self.list_fft_data[self.list_idx] = None
		
		if self.curfft > 0: self.__set_display_image(self.curfft)
		
	def __set_display_image(self,val):
		if self.list_data == None:
			if val > 0 :
				try:
					if self.fft == None:
						self.fft = self.data.do_fft()
						self.fft.set_value_at(0,0,0,0)
						self.fft.set_value_at(1,0,0,0)
					if val==1 :
						self.display_fft = self.fft.process("xform.phaseorigin.tocorner")
						return True
					elif val==2 :
						self.display_fft = self.fft.process("xform.fourierorigin.tocenter")
						self.display_fft = self.display_fft.get_fft_amplitude()
						return True
					elif val==3 :
						self.display_fft = self.fft.process("xform.fourierorigin.tocenter")
						self.display_fft = self.display_fft.get_fft_phase()
						return True
				except: 
					self.display_fft=None
			elif val == 0:
				if self.data == None:
					self.data = self.fft.do_ift()
				return False
			else: 
				self.display_fft=None
	
			return False
		else:
			if val > 0 :
				try:
					if self.list_fft_data[self.list_idx] == None:
						 self.list_fft_data[self.list_idx] = self.list_data[self.list_idx].do_fft()
						
					fft = self.list_fft_data[self.list_idx]
					if val==1 :
						self.display_fft = fft.process("xform.phaseorigin.tocorner")
						return True
					elif val==2 :
						self.display_fft = fft.process("xform.fourierorigin.tocenter")
						self.display_fft = self.display_fft.get_fft_amplitude()
						return True
					elif val==3 :
						self.display_fft = fft.process("xform.fourierorigin.tocenter")
						self.display_fft = self.display_fft.get_fft_phase()
						return True
				except: 
					self.display_fft=None
			elif val == 0:
				if self.list_data[self.list_idx] == None:
					self.list_data[self.list_idx] = self.list_fft_data[self.list_idx].do_ift()
				
				self.data = self.list_data[self.list_idx]
				return False
				
			else: 
				self.display_fft=None
	
			return False
		
	def initializeGL(self):
		emshape.initGL()
		self.init_gl_flag = False

	def force_display_update(self):
		self.display_states = []

	def display_state_changed(self):
		
		display_states = []
		display_states.append(self.gl_widget.width())
		display_states.append(self.gl_widget.height())
		display_states.append(self.origin[0])
		display_states.append(self.origin[1])
		display_states.append(self.scale)
		display_states.append(self.invert)
		display_states.append(self.minden)
		display_states.append(self.maxden)
		display_states.append(self.gamma)
		display_states.append(self.curfft)
		if len(self.display_states) == 0:
			self.display_states = display_states
			return True
		else:
			for i in range(len(display_states)):
				
				if display_states[i] != self.display_states[i]:
					self.display_states = display_states
					return True
		
		return False

	def render(self):
		if not self.data and not self.fft : return
		if self.init_gl_flag: self.initializeGL()
		
		lighting = glIsEnabled(GL_LIGHTING)
		glDisable(GL_LIGHTING)

		if self.shapechange:
			self.setup_shapes()
			self.shapechange=0

		width = self.gl_widget.width()/2.0
		height = self.gl_widget.height()/2.0
		
		if not self.invert : pixden=(0,255)
		else: pixden=(255,0)
		
		if self.otherdata != None and isinstance(self.otherdata,EMData) and not self.glflags.npt_textures_unsupported():
			scale = self.scale*self.otherdatascale
			b=self.otherdata.render_amp8(int(self.origin[0]/scale),int(self.origin[1]/scale),self.gl_widget.width(),self.gl_widget.height(),(self.gl_widget.width()-1)/4*4+4,scale,pixden[0],pixden[1],0,1,1,2)
			gl_render_type = GL_LUMINANCE
			
			if self.other_tex_name != 0: GL.glDeleteTextures(self.other_tex_name)
			self.other_tex_name = GL.glGenTextures(1)
			if ( self.other_tex_name <= 0 ):
				raise("failed to generate texture name")
			
			glBindTexture(GL.GL_TEXTURE_2D,self.other_tex_name)
			glTexImage2D(GL.GL_TEXTURE_2D,0,gl_render_type,self.gl_widget.width(),self.gl_widget.height(),0,gl_render_type, GL.GL_UNSIGNED_BYTE, b)
			
			glPushMatrix()
			glTranslatef(width,height,0)
			self.__draw_texture(self.other_tex_name,-width,-height,width,height)
			glPopMatrix()

		render = False
		if self.use_display_list:
			if self.display_state_changed():
				if self.main_display_list != 0:
					glDeleteLists(self.main_display_list,1)
					self.main_display_list = 0

			if self.main_display_list == 0:
				self.main_display_list = glGenLists(1)
				glNewList(self.main_display_list,GL_COMPILE)
				render = True
		else: render = True
		
		if render:
			if self.curfft==1 :
				if self.display_fft.is_complex() == False:
					print "error, the fft is not complex, internal error"
					return
				a=self.display_fft.render_ap24(int(self.origin[0]/self.scale),int(self.origin[1]/self.scale),self.gl_widget.width(),self.gl_widget.height(),(self.gl_widget.width()*3-1)/4*4+4,self.scale,pixden[0],pixden[1],self.fminden,self.fmaxden,self.fgamma,3)
				gl_render_type = GL_RGB
				
			elif self.curfft in (2,3) :
				a=self.display_fft.render_amp8(int(self.origin[0]/self.scale),int(self.origin[1]/self.scale),self.gl_widget.width(),self.gl_widget.height(),(self.gl_widget.width()-1)/4*4+4,self.scale,pixden[0],pixden[1],self.fminden,self.fmaxden,self.fgamma,2)
				gl_render_type = GL_LUMINANCE
			else : 
				a=self.data.render_amp8(int(self.origin[0]/self.scale),int(self.origin[1]/self.scale),self.gl_widget.width(),self.gl_widget.height(),(self.gl_widget.width()-1)/4*4+4,self.scale,pixden[0],pixden[1],self.minden,self.maxden,self.gamma,2)
				gl_render_type = GL_LUMINANCE
			if not self.glflags.npt_textures_unsupported():
				
				self.hist=struct.unpack('256i',a[-1024:])
			
				if self.tex_name != 0: glDeleteTextures(self.tex_name)
				self.tex_name = glGenTextures(1)
				if ( self.tex_name <= 0 ):
					raise("failed to generate texture name")
				
				if self.otherdatablend and self.otherdata != None:
					GL.glEnable(GL.GL_BLEND);
					depth_testing_was_on = GL.glIsEnabled(GL.GL_DEPTH_TEST);
					GL.glDisable(GL.GL_DEPTH_TEST);
					try:
						GL.glBlendEquation(GL.GL_FUNC_SUBTRACT);
					except: pass
					#GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA);
					GL.glBlendFunc(GL.GL_ONE,GL.GL_ONE);
	
				GL.glBindTexture(GL.GL_TEXTURE_2D,self.tex_name)
				GL.glTexImage2D(GL.GL_TEXTURE_2D,0,gl_render_type,self.gl_widget.width(),self.gl_widget.height(),0,gl_render_type, GL.GL_UNSIGNED_BYTE, a)
				
				glPushMatrix()
				glTranslatef(width,height,0)
				self.__draw_texture(self.tex_name,-width,-height,width,height)
				glPopMatrix()
				
				if self.otherdatablend and self.otherdata != None:
					GL.glDisable( GL.GL_BLEND);
					if (depth_testing_was_on):	GL.glEnable(GL.GL_DEPTH_TEST)
			
			else:
				offset = self.parent.get_viewport_offset()
				GL.glRasterPos(0,self.gl_widget.height()-1)
				GL.glPixelZoom(1.0,-1.0)
				GL.glDrawPixels(self.gl_widget.width(),self.gl_widget.height(),gl_render_type,GL.GL_UNSIGNED_BYTE,a)
		else:
			glCallList(self.main_display_list)
		
		if self.use_display_list and render :
			glEndList()
			glCallList(self.main_display_list)
		
		if self.frozen or self.isexcluded:
			if self.isexcluded:	glColor(0,0.1,0,1)
			else:glColor(0,0,0.1,1)
			
			glPushMatrix()
			glTranslatef(width,height,0)
			self.__draw_square_shaded_region(-width,-height,width,height)
			glPopMatrix()
			
		if self.inspector:
			if self.invert: self.inspector.set_hist(self.hist,self.maxden,self.minden) 
			else: self.inspector.set_hist(self.hist,self.minden,self.maxden)
	
		if self.shapelist != 0:
			GL.glPushMatrix()
			GL.glTranslate(-self.origin[0],-self.origin[1],0.1)
			GL.glScalef(self.scale,self.scale,1.0)
			if self.hack_shrink != 1:
	#			print len(self.shapes),self.hack_shrink
	#			print self.hack_shrink
				GL.glScale(1.0/self.hack_shrink,1.0/self.hack_shrink,1.0)
				#for k,s in self.shapes.items():
					#if self.active[0]==k: s.draw(None,self.active[1:])
					#else: s.draw()
			#else:
				##print self.shapelist
			GL.glCallList(self.shapelist)
			GL.glPopMatrix()
		
		self.__draw_hud()

		if ( lighting ): glEnable(GL_LIGHTING)
	
	def __draw_texture(self,texture_handle,xmin,ymin,xmax,ymax):
		
		texture_2d_was_enabled = GL.glIsEnabled(GL_TEXTURE_2D)
		if not texture_2d_was_enabled:glEnable(GL_TEXTURE_2D)
		
		glBindTexture(GL_TEXTURE_2D, texture_handle)
		#glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		#glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		# using GL_NEAREST ensures pixel granularity
		# using GL_LINEAR blurs textures and makes them more difficult
		# to interpret (in cryo-em)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		# this makes it so that the texture is impervious to lighting
		#glTexEnvfv(GL_TEXTURE_ENV, GL_TEXTURE_ENV_COLOR, [0.2,0.4,0.8,0.5])
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		
		# POSITIONING POLICY - the texture occupies the entire screen area
		glBegin(GL_QUADS)
		
		glTexCoord2f(0,0)
		glVertex2f(xmin,ymax)
		
		glTexCoord2f(1,0)
		glVertex2f(xmax,ymax)
			
		glTexCoord2f(1,1)
		glVertex2f(xmax,ymin)
		
		glTexCoord2f(0,1)
		glVertex2f(xmin,ymin)
			
		glEnd()
		
		if not texture_2d_was_enabled:glDisable(GL_TEXTURE_2D)
			
	
	def __draw_square_shaded_region(self,xmin,ymin,xmax,ymax):
		
		GL.glEnable(GL.GL_BLEND);
		depth_testing_was_on = GL.glIsEnabled(GL.GL_DEPTH_TEST);
		GL.glDisable(GL.GL_DEPTH_TEST)
		GL.glBlendEquation(GL.GL_FUNC_ADD)
		#GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA);
		GL.glBlendFunc(GL.GL_ONE,GL.GL_ONE)
		glBegin(GL_QUADS)
		
		glVertex2f(xmin,ymax)

		glVertex2f(xmax,ymax)
			
		glVertex2f(xmax,ymin)

		glVertex2f(xmin,ymin)
			
		glEnd()
		
		glDisable(GL_TEXTURE_2D)
			
		glDisable( GL.GL_BLEND)
		if (depth_testing_was_on):	GL.glEnable(GL.GL_DEPTH_TEST)
		
	def resizeEvent(self,width,height):
		if self.init_size :
			if self.origin == (0,0):
				#self.origin = ((self.data.get_xsize() - self.gl_widget.width())/2.0, (self.data.get_ysize() - self.gl_widget.height())/2.0 )
				self.oldsize=(width,height)
			self.init_size = False
		else:
			if self.origin == (0,0):
				#self.origin=((self.oldsize[0]/2.0+self.origin[0])-self.gl_widget.width()/2.0,(self.oldsize[1]/2.0+self.origin[1])-self.gl_widget.height()/2.0)
				self.oldsize=(width,height)
				
		self.window_width = width
		self.window_height = height

	def get_shapes(self):
		return self.shapes
	
	def setup_shapes(self):
		if self.shapelist != 0: GL.glDeleteLists(self.shapelist,1)
		
		self.shapelist = glGenLists(1)
		
		#context = OpenGL.contextdata.getContext(None)
		#print "Image2D context is", context,"display list is",self.shapelist
		
		# make our own cirle rather than use gluDisk or somesuch
		glNewList(self.shapelist,GL_COMPILE)
		for k,s in self.shapes.items():
			if self.active[0]==k: s.draw(None,self.active[1:])
			else: s.draw()
		glEndList()
	
	def inspector_update(self,use_fourier=False):
		if self.inspector:
			if not use_fourier:
				self.inspector.set_minden(self.minden)
				self.inspector.set_maxden(self.maxden)
				self.inspector.set_gamma(self.gamma)
			else:
				self.inspector.set_minden(self.fminden)
				self.inspector.set_maxden(self.fmaxden)
				self.inspector.set_gamma(self.fgamma)
				
			self.inspector.set_scale(self.scale)
			self.inspector.update_brightness_contrast()
	
	def get_inspector(self):
		if not self.inspector:
			self.inspector=EMImageInspector2D(self)
			self.inspector_update()
		return self.inspector
	

	def set_active(self,n,r,g,b):
		self.active=(n,r,g,b)
		self.shapechange=1
		#self.updateGL()

	def update_animation(self):
		
		if not self.isanimated:
			return False
		
		self.time += self.timeinc
		if self.time > 1:
			self.time = 1
			self.isanimated = False
			self.set_origin(self.endorigin[0],self.endorigin[1])
			return True
		
		# get time squared
		tinv = 1-self.time
		t1 = tinv**2
		t2 = 1-t1
		
		x = t1*self.startorigin[0] + t2*self.endorigin[0]
		y = t1*self.startorigin[1] + t2*self.endorigin[1]
		self.set_origin(x,y)
		return True

	def animation_done_event(self,animation):
		if isinstance(animation,SingleValueIncrementAnimation):
			self.set_animation_increment(animation.get_end())
		elif isinstance(animation,LineAnimation):
			self.set_line_animation(*animation.get_end())

	def set_animation_increment(self,increment):
		for shape in self.shapes.items():
			shape[1].set_blend(increment)
		
		self.shapechange = True
		
	def set_line_animation(self,x,y):
		self.origin=(x,y)
		self.display_states = [] #forces an display list update
		
	def update_blend(self):
		ret = False
		for shape in self.shapes.items():
			s = shape[1]
			if s.isanimated:
				v = s.incblend()
				ret = True
		
		return ret

	def add_shape(self,k,s):
		"""Add an EMShape object to be overlaid on the image. Each shape is
		keyed into a dictionary, so different types of shapes for different
		purposes may be simultaneously displayed.
		
		"""
		self.shapes[k]=s
		self.shapechange=1
		#self.updateGL()
	
	def add_shapes(self,d,register_animation=False):
		if register_animation:
			animation = SingleValueIncrementAnimation(self,0,1)
			self.get_gl_parent().register_animatable(animation)
		self.shapes.update(d)
		self.shapechange=1
		#self.updateGL()
	
	
	def del_shape(self,p):
		try:
			self.shapes.pop(p)
			self.shapechange=1
		except:pass

	def del_shapes(self,k=None):
		if k:
			try:
				for i in k:
					del self.shapes[k]
			except: del self.shapes[k]
		else:
			self.shapes={}
		self.shapechange=1
		#self.updateGL()
	
	def scr_to_img(self,v0,v1=None):
		try: return ((v0+self.origin[0])/self.scale,(self.gl_widget.height()-(v1-self.origin[1]))/self.scale)
		except:	return ((v0[0]+self.origin[0])/self.scale,(self.gl_widget.height()-(v0[1]-self.origin[1]))/self.scale)

	def closeEvent(self,event) :
		self.__write_display_settings_to_db()
		EMGUIModule.closeEvent(self,event)
		
	def dragEnterEvent(self,event):
#		f=event.mimeData().formats()
#		for i in f:
#			print str(i)
		
		if event.provides("application/x-eman"):
			event.setDropAction(Qt.CopyAction)
			event.accept()

	def dropEvent(self,event):
		if EMAN2.GUIbeingdragged:
			self.set_data(EMAN2.GUIbeingdragged)
			EMAN2.GUIbeingdragged=None
		elif event.provides("application/x-eman"):
			x=loads(event.mimeData().data("application/x-eman"))
			self.set_data(x)
			event.acceptProposedAction()

	def mousePressEvent(self, event):
		lc=self.scr_to_img(event.x(),event.y())
		if event.button()==Qt.MidButton or (event.button()==Qt.LeftButton and event.modifiers()&Qt.ControlModifier):
			self.show_inspector(1)
		elif event.button()==Qt.RightButton or (event.button()==Qt.LeftButton and event.modifiers()&Qt.AltModifier):
			try:
				self.application.setOverrideCursor(Qt.ClosedHandCursor)
			except: # if we're using a version of qt older than 4.2 than we have to use this...
				self.application.setOverrideCursor(Qt.SizeAllCursor)
			self.rmousedrag=(event.x(),event.y() )
		else:
			self.mouse_event_handler.mouse_down(event)

	def mouseMoveEvent(self, event):
		lc=self.scr_to_img(event.x(),event.y())
		if self.rmousedrag:
			self.origin=(self.origin[0]+self.rmousedrag[0]-event.x(),self.origin[1]-self.rmousedrag[1]+event.y())
			self.rmousedrag=(event.x(),event.y())
			try: self.parent.update()
			except: pass
		else:
			self.mouse_event_handler.mouse_move(event)
		
	def mouseReleaseEvent(self, event):
		self.application.setOverrideCursor(Qt.ArrowCursor)
		lc=self.scr_to_img(event.x(),event.y())
		if self.rmousedrag:
			self.rmousedrag=None
		else:
			self.mouse_event_handler.mouse_up(event)

	def wheelEvent(self, event):
		if not self.wheel_navigate:
			if event.orientation() & Qt.Vertical:
				if self.mmode==0 and event.modifiers()&Qt.ShiftModifier:
					self.mouse_event_handler.mouse_wheel(event)
					return
				if event.delta() > 0:
					self.set_scale( self.scale * self.mag )
				elif event.delta() < 0:
					self.set_scale(self.scale * self.invmag )
				# The self.scale variable is updated now, so just update with that
				if self.inspector: self.inspector.set_scale(self.scale)
		else:
			move_fac = 1.0/20.0
			delta = event.delta()/120.0
			
#			print self.origin, self.data.get_xsize(),self.data.get_ysize(),self.scale,self.gl_widget.width(),self.gl_widget.height()

#			print self.origin
			if event.orientation() & Qt.Vertical:
				visible_vertical_pixels = self.gl_widget.height()/sqrt(self.scale)
				shift_per_delta = move_fac*visible_vertical_pixels
#				print "there are this many visible vertical pixels",visible_vertical_pixels, "deltas", delta, "shift per delta",shift_per_delta
#				print "shifting vertical",event.delta(),shift_per_delta
				self.origin=(self.origin[0],self.origin[1]-delta*shift_per_delta)
			elif event.orientation() & Qt.Horizontal:
				visible_horizontal_pixels = self.gl_widget.width()/sqrt(self.scale)
				shift_per_delta = move_fac*visible_horizontal_pixels
#				print "shifting horizontal",event.delta(),shift_per_delta
#	   	   	   	print "there are this many visible horizontal pixels",visible_horizontal_pixels, "deltas", delta, "shift per delta",shift_per_delta
				self.origin=(self.origin[0]+delta*shift_per_delta,self.origin[1])
			try: self.parent.update()
			except: pass
#			print "exit",self.origin
			
	
	def mouseDoubleClickEvent(self,event):
		if platform.system() == "Darwin":
			self.wheel_navigate = not self.wheel_navigate
		else:
			print "double click only performs a function on Mac"

	def keyPressEvent(self,event):
		if event.key() == Qt.Key_F1:
			try:
				try:
					test = self.browser
				except: 
					self.browser = QtWebKit.QWebView()
					self.browser.load(QtCore.QUrl("http://blake.bcm.edu/emanwiki/e2display"))
					self.browser.resize(800,800)
				
				if not self.browser.isVisible(): self.browser.show()
			except:
				print "in the middle of getting help working"
				self.browser2 = QtGui.QTextBrowser()
				#url = QtCore.QUrl("http://blake.bcm.edu/emanwiki/e2display")
				url = QtCore.QUrl("http://www.google.com")
				url.setPort(80)
				#print url.port()
				self.browser2.setSource(url)
				#print browser2.port()
				self.browser2.show()
				self.browser2.resize(800,800)
				
		elif event.key() == Qt.Key_Up:
			if self.list_data != None:
				if (self.list_idx < (len(self.list_data)-1)):
					self.list_idx += 1
					self.get_inspector().set_image_idx(self.list_idx+1)
					self.__set_display_image(self.curfft)
					self.force_display_update()
					self.updateGL()
		elif event.key() == Qt.Key_Down:
			if self.list_data != None:
				if (self.list_idx > 0):
					self.list_idx -= 1
					self.get_inspector().set_image_idx(self.list_idx+1)
					self.__set_display_image(self.curfft)
					self.force_display_update()
					self.updateGL()

	def image_range_changed(self,val):
		l_val = val-1
		
		if l_val == self.list_idx: return
		else:
			self.list_idx = l_val
			self.__set_display_image(self.curfft)
			self.force_display_update()
			self.updateGL()

	def leaveEvent(self):
		if self.rmousedrag:
			self.rmousedrag=None
		
	def __draw_hud(self):
		if self.list_data == None: return
		
		if self.font_renderer == None:
			self.__init_font_renderer()
			
		
		width = self.gl_widget.width()
		height = self.gl_widget.height()
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0,width,0,height,-100,100)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glEnable(GL_LIGHTING)
		glEnable(GL_NORMALIZE)
		glMaterial(GL_FRONT,GL_AMBIENT,(0.2, 1.0, 0.2,1.0))
		glMaterial(GL_FRONT,GL_DIFFUSE,(0.2, 1.0, 0.9,1.0))
		glMaterial(GL_FRONT,GL_SPECULAR,(1.0	, 0.5, 0.2,1.0))
		glMaterial(GL_FRONT,GL_SHININESS,20.0)
		enable_depth = glIsEnabled(GL_DEPTH_TEST)
		glDisable(GL_DEPTH_TEST)
		glColor(1.0,1.0,1.0)
		
		
		if self.font_render_mode == EMGUIModule.FTGL:
			n = len(self.list_data)
			string = str(self.list_idx+1) + ' / ' + str(n)
			bbox = self.font_renderer.bounding_box(string)
			x_offset = width-(bbox[3]-bbox[0]) - 10
			y_offset = 10
			
			glPushMatrix()
			glTranslate(x_offset,y_offset,0)
			glRotate(20,0,1,0)
			self.font_renderer.render_string(string)
			glPopMatrix()
			#y_offset += bbox[4]-bbox[1]

		if enable_depth: glEnable(GL_DEPTH_TEST)
		
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
	
	
	def __init_font_renderer(self):
		try:
			self.font_renderer = get_3d_font_renderer()
			self.font_renderer.set_face_size(20)
			self.font_renderer.set_depth(4)
			self.font_renderer.set_font_mode(FTGLFontMode.EXTRUDE)
			
#			self.font_renderer.set_font_file_name("/usr/share/fonts/dejavu/DejaVuSerif.ttf")
			self.font_render_mode = EMGUIModule.FTGL
		except:
			self.font_render_mode = EMGUIModule.GLUT
	
class EMImageInspector2D(QtGui.QWidget):
	def get_desktop_hint(self):
		return "inspector"
	
	def __init__(self,target) :
		QtGui.QWidget.__init__(self,None)
		self.target=target
		
		self.vbl = QtGui.QVBoxLayout(self)
		self.vbl.setMargin(2)
		self.vbl.setSpacing(6)
		self.vbl.setObjectName("vbl")
		
		# This is the tab-bar for mouse mode selection
		self.mmtab = QtGui.QTabWidget()
		
		# App tab
		self.apptab = QtGui.QWidget()
		self.apptablab = QtGui.QLabel("Application specific mouse functions",self.apptab)
		self.mmtab.addTab(self.apptab,"App")
		
		# Measure tab
		self.meastab = QtGui.QWidget()
		self.mtlay = QtGui.QGridLayout(self.meastab)
		
		#self.mtl1= QtGui.QLabel("A/Pix")
		#self.mtl1.setAlignment(Qt.AlignRight)
		#self.mtlay.addWidget(self.mtl1,0,0)
		
		self.mtapix = ValSlider(self,label="A/Pix")
		self.mtapix.setRange(0.5,10.0)
		self.mtapix.setValue(1.0)
		self.mtlay.addWidget(self.mtapix,0,0,1,2)
#		self.mtapix.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
#		self.mtapix.resize(60,21)
#		print self.mtapix.sizeHint().width(),self.mtapix.sizeHint().height()
		
		self.mtshowlen= QtGui.QLabel("Length:")
		self.mtlay.addWidget(self.mtshowlen,2,0,1,2,Qt.AlignHCenter)
		
		self.mtshoworigin= QtGui.QLabel("Origin:")
		self.mtlay.addWidget(self.mtshoworigin,1,0,Qt.AlignHCenter)
		
		self.mtshowend= QtGui.QLabel("End:")
		self.mtlay.addWidget(self.mtshowend,1,1,Qt.AlignHCenter)
		
		self.mmtab.addTab(self.meastab,"Meas")
		
		# Draw tab
		self.drawtab = QtGui.QWidget()
		self.drawlay = QtGui.QGridLayout(self.drawtab)
		
		self.dtl1 = QtGui.QLabel("Pen Size:")
		self.dtl1.setAlignment(Qt.AlignRight)
		self.drawlay.addWidget(self.dtl1,0,0)
		
		self.dtpen = QtGui.QLineEdit("5")
		self.drawlay.addWidget(self.dtpen,0,1)
		
		self.dtl2 = QtGui.QLabel("Pen Val:")
		self.dtl2.setAlignment(Qt.AlignRight)
		self.drawlay.addWidget(self.dtl2,1,0)
		
		self.dtpenv = QtGui.QLineEdit("1.0")
		self.drawlay.addWidget(self.dtpenv,1,1)
		
		self.dtl3 = QtGui.QLabel("Pen Size2:")
		self.dtl3.setAlignment(Qt.AlignRight)
		self.drawlay.addWidget(self.dtl3,0,2)
		
		self.dtpen2 = QtGui.QLineEdit("5")
		self.drawlay.addWidget(self.dtpen2,0,3)
		
		self.dtl4 = QtGui.QLabel("Pen Val2:")
		self.dtl4.setAlignment(Qt.AlignRight)
		self.drawlay.addWidget(self.dtl4,1,2)
		
		self.dtpenv2 = QtGui.QLineEdit("0")
		self.drawlay.addWidget(self.dtpenv2,1,3)
		
		self.mmtab.addTab(self.drawtab,"Draw")
		
		self.vbl.addWidget(self.mmtab)
		
		# histogram level horiz layout
		self.hbl = QtGui.QHBoxLayout()
		self.hbl.setMargin(0)
		self.hbl.setSpacing(6)
		self.hbl.setObjectName("hbl")
		self.vbl.addLayout(self.hbl)
		
		self.hist = ImgHistogram(self)
		self.hist.setObjectName("hist")
		self.hbl.addWidget(self.hist)
		
		# Buttons next to the histogram
		self.vbl2 = QtGui.QGridLayout()
		self.vbl2.setMargin(0)
		self.vbl2.setSpacing(6)
		self.vbl2.setObjectName("vbl2")
		self.hbl.addLayout(self.vbl2)
		
		self.invtog = QtGui.QPushButton("Invert")
		self.invtog.setCheckable(1)
		self.vbl2.addWidget(self.invtog,0,0,1,2)
		
		self.auto_contrast_button = QtGui.QPushButton("Auto contrast")
		self.vbl2.addWidget(self.auto_contrast_button,1,0,1,2)
		
		# FFT Buttons
		self.fftg=QtGui.QButtonGroup()
		self.fftg.setExclusive(1)
		
		self.ffttog0 = QtGui.QPushButton("Real")
		self.ffttog0.setCheckable(1)
		self.ffttog0.setChecked(1)
		self.vbl2.addWidget(self.ffttog0,2,0)
		self.fftg.addButton(self.ffttog0,0)

		self.ffttog1 = QtGui.QPushButton("FFT")
		self.ffttog1.setCheckable(1)
		self.vbl2.addWidget(self.ffttog1,2,1)
		self.fftg.addButton(self.ffttog1,1)

		self.ffttog2 = QtGui.QPushButton("Amp")
		self.ffttog2.setCheckable(1)
		self.vbl2.addWidget(self.ffttog2,3,0)
		self.fftg.addButton(self.ffttog2,2)
		
		self.ffttog3 = QtGui.QPushButton("Pha")
		self.ffttog3.setCheckable(1)
		self.vbl2.addWidget(self.ffttog3,3,1)
		self.fftg.addButton(self.ffttog3,3)
	
		self.scale = ValSlider(self,(0.1,5.0),"Mag:")
		self.scale.setObjectName("scale")
		self.scale.setValue(1.0)
		self.vbl.addWidget(self.scale)
		
		self.mins = ValSlider(self,label="Min:")
		self.mins.setObjectName("mins")
		self.mins.setValue(self.target.get_minden())
		self.vbl.addWidget(self.mins)
		
		self.maxs = ValSlider(self,label="Max:")
		self.maxs.setObjectName("maxs")
		self.maxs.setValue(self.target.get_maxden())
		self.vbl.addWidget(self.maxs)
		
		self.brts = ValSlider(self,(-1.0,1.0),"Brt:")
		self.brts.setObjectName("brts")
		#self.brts.setValue(0.0)
		self.vbl.addWidget(self.brts)
		
		self.conts = ValSlider(self,(0.0,1.0),"Cont:")
		self.conts.setObjectName("conts")
		self.conts.setValue(1.0)
		self.vbl.addWidget(self.conts)
		
		self.gammas = ValSlider(self,(.1,5.0),"Gam:")
		self.gammas.setObjectName("gamma")
		self.gammas.setValue(self.target.get_gamma())
		#self.gammas.setValue(1.0)
		self.vbl.addWidget(self.gammas)

		self.setWindowIcon(QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/eman.png"))

		self.lowlim=0
		self.highlim=1.0
		self.image_range = None
		#self.update_min_max()
		#self.update_brightness_contrast()
		self.busy=0
		
		QtCore.QObject.connect(self.scale, QtCore.SIGNAL("valueChanged"), target.set_scale)
		QtCore.QObject.connect(self.mins, QtCore.SIGNAL("valueChanged"), self.new_min)
		QtCore.QObject.connect(self.maxs, QtCore.SIGNAL("valueChanged"), self.new_max)
		QtCore.QObject.connect(self.brts, QtCore.SIGNAL("valueChanged"), self.new_brt)
		QtCore.QObject.connect(self.conts, QtCore.SIGNAL("valueChanged"), self.new_cont)
		QtCore.QObject.connect(self.gammas, QtCore.SIGNAL("valueChanged"), self.new_gamma)
		QtCore.QObject.connect(self.invtog, QtCore.SIGNAL("toggled(bool)"), target.set_invert)
		QtCore.QObject.connect(self.fftg, QtCore.SIGNAL("buttonClicked(int)"), target.set_FFT)
		QtCore.QObject.connect(self.mmtab, QtCore.SIGNAL("currentChanged(int)"), target.set_mouse_mode)
		QtCore.QObject.connect(self.auto_contrast_button, QtCore.SIGNAL("clicked(bool)"), target.auto_contrast)
#		QtCore.QObject.connect(self.mmode, QtCore.SIGNAL("buttonClicked(int)"), target.set_mouse_mode)


	def disable_image_range(self):
		if self.image_range != None:
			self.vbl.removeWidget(self.image_range)
			self.image_range.deleteLater()
			self.image_range = None
		else:
			# this is fine
			pass
			#print "warning, attempted to disable image range when there was none!"

	def enable_image_range(self,minimum,maximum,current_idx):
		if self.image_range == None:
			self.image_range = ValSlider(self,label="N#:")
			self.image_range.setIntonly(True)
			self.vbl.addWidget(self.image_range)
			
		self.image_range.setRange(minimum,maximum)
		self.image_range.setValue(current_idx)
		
		QtCore.QObject.connect(self.image_range, QtCore.SIGNAL("valueChanged"), self.target.image_range_changed)

	def set_image_idx(self,val):
		self.image_range.setValue(val)

	def set_fft_amp_pressed(self):
		self.ffttog2.setChecked(1)

	def get_contrast(self):
		return float(self.conts.getValue())
	
	def get_brightness(self):
		return float(self.brts.getValue())
	
	#def set_contrast(self,value,quiet=1):
		#self.conts.setValue(value,quiet)
		
	#def set_brightness(self,value,quiet=1):
		#self.brts.setValue(value,quiet)
		
	def set_maxden(self,value,quiet=1):
		self.maxs.setValue(value,quiet)
		
	def set_minden(self,value,quiet=1):
		self.mins.setValue(value,quiet)
		
	def set_gamma(self,value,quiet=1):
		self.gammas.setValue(value,quiet)
	
	def set_scale(self,val):
		if self.busy : return
		self.busy=1
		self.scale.setValue(val)
		self.busy=0

	def new_min(self,val):
		if self.busy : return
		self.busy=1
		self.target.set_density_min(val)
		self.update_brightness_contrast()
		self.busy=0
		
	def new_max(self,val):
		if self.busy : return
		self.busy=1
		self.target.set_density_max(val)
		self.update_brightness_contrast()
		self.busy=0
	
	def new_brt(self,val):
		if self.busy : return
		self.busy=1
		self.update_min_max()
		self.busy=0
		
	def new_cont(self,val):
		if self.busy : return
		self.busy=1
		self.update_min_max()
		self.busy=0
		
	def new_gamma(self,val):
		if self.busy : return
		self.busy=1
		self.target.set_gamma(val)
		self.busy=0

	def update_brightness_contrast(self):
		b=0.5*(self.mins.value+self.maxs.value-(self.lowlim+self.highlim))/((self.highlim-self.lowlim))
		c=(self.mins.value-self.maxs.value)/(2.0*(self.lowlim-self.highlim))
		brts = -b
		conts = 1.0-c
		self.brts.setValue(brts)
		self.conts.setValue(conts)
		
	def update_min_max(self):
		
		x0=((self.lowlim+self.highlim)/2.0-(self.highlim-self.lowlim)*(1.0-self.conts.value)-self.brts.value*(self.highlim-self.lowlim))
		x1=((self.lowlim+self.highlim)/2.0+(self.highlim-self.lowlim)*(1.0-self.conts.value)-self.brts.value*(self.highlim-self.lowlim))
		self.mins.setValue(x0)
		self.maxs.setValue(x1)
		self.target.set_density_range(x0,x1)
		
	def set_hist(self,hist,minden,maxden):
		if hist != None and len(hist) != 0:self.hist.set_data(hist,minden,maxden)

	def set_limits(self,lowlim,highlim,curmin,curmax):
		if highlim<=lowlim : highlim=lowlim+.001
		#print "in set limits", self.conts.getValue(), self.conts.getValue()
		self.lowlim=lowlim
		self.highlim=highlim
		self.mins.setRange(lowlim,highlim)
		self.maxs.setRange(lowlim,highlim)
		self.mins.setValue(curmin)
		self.maxs.setValue(curmax)
		self.target.set_density_range(curmin,curmax)
		#print "leave set limits", self.conts.getValue(), self.conts.getValue()
		

# This is just for testing, of course
if __name__ == '__main__':
	em_app = EMStandAloneApplication()
	window = EMImage2DModule(application=em_app)
	
	if len(sys.argv)==1 : 
		window.set_data(test_image(size=(128,128)))
	else :
		a=EMData.read_images(sys.argv[1],[0])
		if len(a) == 1:
			a = a[0]
			data = []
			if a.get_ndim() == 3:
				for z in range(a.get_zsize()):
					image = a.get_clip(Region(0,0,z,a.get_xsize(),a.get_ysize(),1))
					data.append(image)
				a  = data
		window.set_data(a)
		
		window.set_file_name(sys.argv[1])
		
	em_app.show()
	em_app.execute()
	

