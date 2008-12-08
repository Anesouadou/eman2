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
from emshape import *
from emimageutil import ImgHistogram,EMParentWin
from weakref import WeakKeyDictionary
import weakref
from pickle import dumps,loads
import struct
import traceback

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
#matplotlib.use('Agg')

from emapplication import EMStandAloneApplication, EMGUIModule
from emimageutil import EMEventRerouter, EMParentWin
from emglobjects import EMOpenGLFlagsAndTools

linetypes=["-","--",":","-."]
symtypes=["o","s","+","2","1"]
colortypes=["k","b","r","g"]


class EMPlot2DWidget(QtOpenGL.QGLWidget,EMEventRerouter,):
	"""A QT widget for drawing 2-D plots using matplotlib
	"""
	def __init__(self, em_plot_module):
		assert(isinstance(em_plot_module,EMPlot2DModule))
		fmt=QtOpenGL.QGLFormat()
		fmt.setDoubleBuffer(True);
		QtOpenGL.QGLWidget.__init__(self,fmt, None)
		EMEventRerouter.__init__(self,em_plot_module) # sets self.target to em_plot_module

		self.resize(480,480)
	def initializeGL(self):
		GL.glClearColor(0,0,0,0)
		GL.glEnable(GL_DEPTH_TEST)
	def paintGL(self):
		if not self.parentWidget() : return
		GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
		
		GL.glMatrixMode(GL.GL_MODELVIEW)
		GL.glLoadIdentity()
		self.target().render()
		
	def resizeGL(self, width, height):
#		print "resize ",self.width()
		side = min(width, height)
		GL.glViewport(0,0,self.width(),self.height())
	
		
		
		GL.glMatrixMode(GL.GL_PROJECTION)
		GL.glLoadIdentity()
		GL.glOrtho(0.0,self.width(),0.0,self.height(),-10,10)
		GL.glMatrixMode(GL.GL_MODELVIEW)
		GL.glLoadIdentity()
		
		self.target().resize_event(width,height)
	def closeEvent(self,event):
		self.target().clear_gl_memory()
		self.target().closeEvent(None)
		
	def keyPressEvent(self,event):
		if event.key() == Qt.Key_F1:
			try: from PyQt4 import QtWebKit
			except: return
			try:
				try:
					test = self.browser
				except: 
					self.browser = QtWebKit.QWebView()
					self.browser.load(QtCore.QUrl("http://blake.bcm.edu/emanwiki/e2display"))
					self.browser.resize(800,800)
				
				if not self.browser.isVisible(): self.browser.show()
			except: pass
		else:
			EMEventRerouter.keyPressEvent(self,event)
		
class EMPlot2DModule(EMGUIModule):

	def get_desktop_hint(self):
		return "plot"

	def get_qt_widget(self):
		if self.qt_context_parent == None:	
			self.under_qt_control = True
			self.gl_context_parent = EMPlot2DWidget(self)
			self.qt_context_parent = EMParentWin(self.gl_context_parent)
			self.gl_widget = self.gl_context_parent
			self.qt_context_parent.setWindowIcon(QtGui.QIcon(get_image_directory() +"plot.png"))
		return self.qt_context_parent
	
	def get_gl_widget(self,qt_context_parent,gl_context_parent):
		from emfloatingwidgets import EM2DGLView, EM2DGLWindow
		self.init_size_flag = False
		if self.gl_widget == None:
			self.under_qt_control = False
			self.gl_context_parent = gl_context_parent
			self.qt_context_parent = qt_context_parent
			
			gl_view = EM2DGLView(self,image=None)
			self.gl_widget = EM2DGLWindow(self,gl_view)
			self.gl_widget.target_translations_allowed(True)
			self.gl_widget.setWindowTitle("2D Plot")
			
		return self.gl_widget
	
	
	def __init__(self,application=None):
		EMGUIModule.__init__(self,application)
		self.axes={}
		self.pparm={}
		self.inspector=None
		self.needupd=1
		self.plotimg=None
		self.shapes={}
		self.limits=None
		self.rmousedrag=None
		self.axisparms=(None,None,"linear","linear")
		
		self.data={}				# List of Lists to plot 
		self.glflags = EMOpenGLFlagsAndTools() 	# supplies power of two texturing flags
		
		self.tex_name = 0
		self.main_display_list = 0
	
	def clear_gl_memory(self):
		if self.tex_name != 0: 
			GL.glDeleteTextures(self.tex_name)
			self.tex_name = 0
		if self.main_display_list != 0:
			glDeleteLists(self.main_display_list,1)
			self.main_display_list = 0
	
	def __del__(self):

		self.clear_gl_memory()
	
	def set_data(self,key,input_data,replace=False,quiet=False):
		"""Set a keyed data set. The key should generally be a string describing the data.
		'data' is a tuple/list of tuples/list representing all values for a particular
		axis. eg - the points: 1,5; 2,7; 3,9 would be represented as ((1,2,3),(5,7,9)).
		Multiple axes may be set, and which axis represents which axis in the plot can be
		selected by the user. 'data' can also be an EMData object, in which case the entire
		data array is plotted as if it were 1-D."""
		
		self.needupd=1
		
		if replace: 
			self.data = {}
			self.axes = {}
		if isinstance(input_data,EMData):
			data = input_data.get_data_as_vector()
		else: data = input_data
		
		try:
			if len(data)>1 : self.axes[key]=(0,1,-1)
			else : self.axes[key]=(-1,0,-1)
		except: return
		
		self.pparm[key]=(0,1,0,1,0,0,5)
		
		if not isinstance(data[0],list):
			x_axis = [i for i in range(len(data))]
			rdata = [ x_axis,data ]
			self.data[key]= rdata
		else:
			if data : self.data[key]=data
			else : del self.data[key]
		
		
		if self.inspector: self.inspector.datachange()
		
		if not quiet: self.updateGL()
	
	def get_inspector(self):
		if not self.inspector :
			self.inspector=EMPlot2DInspector(self)
			self.inspector.datachange()
		return self.inspector
	
	
	def width(self):
		try: return self.gl_widget.width()
		except: pass
		
	def height(self):
		try: return self.gl_widget.height()
		except: pass
	
	def updateGL(self):
		if  self.gl_widget != None and self.under_qt_control: self.gl_widget.updateGL()
		
	def set_data_from_file(self,filename,replace=False):
		"""Reads a keyed data set from a file. Automatically interpret the file contents."""
		
		if replace: 
			self.data = {}
			self.axes = {}
		
		file_type = Util.get_filename_ext(filename)
		em_file_type = EMUtil.get_image_ext_type(file_type)
		
		if em_file_type != IMAGE_UNKNOWN:
			
			im=EMData.read_images(filename)
			if len(im) == 1:
				im = im[0]
				l = [i for i in range(im.get_size())]
				k = im.get_data_as_vector()
				self.set_data(filename,[l,k])
			else:
				for idx,image in enumerate(im):
					l = [i for i in range(image.get_size())]
					k = image.get_data_as_vector()
					self.set_data("Image "+str(idx),[l,k])
				
		elif file_type == 'fp':
			fin=file(filename)
			fph=struct.unpack("120sII",fin.read(128))
			ny=fph[1]
			nx=fph[2]
			data=[]
			for i in range(nx):
				data.append(struct.unpack("%df"%ny,fin.read(4*ny)))
				
			self.set_data(filename,data)
		else:
			try:
				fin=file(filename)
				fin.seek(0)
				rdata=fin.readlines()
				rdata=[i for i in rdata if i[0]!='#']
				if ',' in rdata[0]: rdata=[[float(j) for j in i.split(',')] for i in rdata]
				else : rdata=[[float(j) for j in i.split()] for i in rdata]
				nx=len(rdata[0])
				ny=len(rdata)
				data=[[rdata[j][i] for j in range(ny)] for i in range(nx)]
					
				self.set_data(remove_directories_from_name(filename),data)
			except:
				print "couldn't read",filename
				return False
				
		return True

	def is_file_readable(self,filename):
		'''
		Called by file browsing interfaces to determine if the file is plottable
		Tries to parse two lines, convert the values into floats, make sure
		the number of columns matches etc. If something goes wrong then return False.
		This function should be tightly coupled to set_data_from_file function, should
		any adaptations occur in future
		'''
		try:
			fin=file(filename)
			fin.seek(0)
			rdata = []
			while (len(rdata) < 2):
				line = fin.readline()
				if line == '': # this is equivalent to EOF
					break
				elif line[0] == '#': continue
				else: rdata.append(line)
				
			#print rdata
			if len(rdata) < 2: return False

			if ',' in rdata[0]: rdata=[[float(j) for j in i.split(',')] for i in rdata]
			else : rdata=[[float(j) for j in i.split()] for i in rdata]
			
			if len(rdata[0]) == 0 or len(rdata[1]) == 0: return False
			if  len(rdata[0]) != len(rdata[1]) : return False

			return True
			
		except:
			#print "couldn't read",filename
			return False

	def render(self):
		if not self.data : return
		
		render = False
			
		if self.needupd or not self.plotimg:
			self.needupd=0
			if self.main_display_list != 0:
				glDeleteLists(self.main_display_list,1)
				self.main_display_list = 0

		if self.main_display_list == 0:
			self.main_display_list = glGenLists(1)
			glNewList(self.main_display_list,GL_COMPILE)
			render = True

		lighting = glIsEnabled(GL_LIGHTING)
		glDisable(GL_LIGHTING)
		
		GL.glPushMatrix()
		glTranslate(0,0,5)
		for k,s in self.shapes.items():
			#print s
			s.draw(self.scr2plot)
		GL.glPopMatrix()
		
		if render: 

			fig=Figure((self.width()/72.0,self.height()/72.0),dpi=72.0)
			if self.limits :ax=fig.add_axes((.08,.08,.9,.9),autoscale_on=False,xlim=self.limits[0],ylim=self.limits[1],xscale=self.axisparms[2],yscale=self.axisparms[3])
			else : ax=fig.add_axes((.08,.08,.9,.9),autoscale_on=True,xscale=self.axisparms[2],yscale=self.axisparms[3])
			if self.axisparms[0] and len(self.axisparms[0])>0 : ax.set_xlabel(self.axisparms[0],size="xx-large")
			if self.axisparms[1] and len(self.axisparms[1])>0 : ax.set_ylabel(self.axisparms[1],size="xx-large")
			canvas=FigureCanvasAgg(fig)
			
			for i in self.axes.keys():
				j=self.axes[i]
				if j[0]==-1 : x=range(len(self.data[i][0]))
				else : x=self.data[i][self.axes[i][0]]
				if j[1]==-1 : y=range(len(self.data[i][0]))
				else : y=self.data[i][self.axes[i][1]]
				parm=""
				parm+=colortypes[self.pparm[i][0]]
				if self.pparm[i][1]: 
					parm+=linetypes[self.pparm[i][2]]
				if self.pparm[i][4]:
					parm+=symtypes[self.pparm[i][5]]
					
				ax.plot(x,y,parm,linewidth=self.pparm[i][3],markersize=self.pparm[i][6])
			
			
			canvas.draw()
			self.plotimg = canvas.tostring_rgb()  # save this and convert to bitmap as needed
			
			# this try except block is because the developers of matplotlib have been changing their API
			try: # this would work for matplotlib 0.98
				self.scrlim=(ax.get_window_extent().xmin,ax.get_window_extent().ymin,ax.get_window_extent().xmax-ax.get_window_extent().xmin,ax.get_window_extent().ymax-ax.get_window_extent().ymin)
			except:
				try: # this should work for matplotlib 0.91
					self.scrlim=(ax.get_window_extent().xmin(),ax.get_window_extent().ymin(),ax.get_window_extent().xmax()-ax.get_window_extent().xmin(),ax.get_window_extent().ymax()-ax.get_window_extent().ymin())
				except:
					print 'there is a problem with your matplotlib'
					return
			self.plotlim=(ax.get_xlim()[0],ax.get_ylim()[0],ax.get_xlim()[1]-ax.get_xlim()[0],ax.get_ylim()[1]-ax.get_ylim()[0])
			
	#		print ax.get_window_extent().xmin(),ax.get_window_extent().ymin()
	#		print ax.get_window_extent().xmax(),ax.get_window_extent().ymax()
	#		print ax.get_position()
			if not self.glflags.npt_textures_unsupported():
				self.__texture_plot(self.plotimg)
			else:
				print "rastering"
				GL.glRasterPos(0,self.height()-1)
				GL.glPixelZoom(1.0,-1.0)
		#		print "paint ",self.width(),self.height(), self.width()*self.height(),len(a)
				GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT,1)
				GL.glDrawPixels(self.width(),self.height(),GL.GL_RGB,GL.GL_UNSIGNED_BYTE,self.plotimg)
		else:
			try:
				glCallList(self.main_display_list)
			except: pass
		
		if render :
			glEndList()
			glCallList(self.main_display_list)

		
		
		if lighting : glEnable(GL_LIGHTING)
		
		
	def __texture_plot(self,image_data):
		
		
		texture_2d_was_enabled = GL.glIsEnabled(GL.GL_TEXTURE_2D)
		if not texture_2d_was_enabled:GL.glEnable(GL.GL_TEXTURE_2D)
		
		if self.tex_name != 0: GL.glDeleteTextures(self.tex_name)
		self.tex_name = GL.glGenTextures(1)
		GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT,1)
		GL.glBindTexture(GL.GL_TEXTURE_2D,self.tex_name)
		GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGB,self.width(),self.height(),0,GL.GL_RGB,GL.GL_UNSIGNED_BYTE, image_data)
		
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		
		# POSITIONING POLICY - the texture occupies the entire screen area
		glBegin(GL_QUADS)
		
		glTexCoord2f(0,0)
		glVertex2f(0,self.height())
		
		glTexCoord2f(1,0)
		glVertex2f(self.width(),self.height())
			
		glTexCoord2f(1,1)
		glVertex2f(self.width(),0)
		
		glTexCoord2f(0,1)
		glVertex2f(0,0)
			
		glEnd()
		
		if not texture_2d_was_enabled: GL.glDisable(GL.GL_TEXTURE_2D)
	
	def scr2plot(self,x,y) :
		""" converts screen coordinates to plot coordinates """
		try: 
			if self.axisparms[2]=="linear" : x2=(x-self.scrlim[0])/self.scrlim[2]*self.plotlim[2]+self.plotlim[0]
			else : x2=10.0**((x-self.scrlim[0])/self.scrlim[2]*(log10(self.plotlim[2]+self.plotlim[0])-log10(self.plotlim[0]))+log10(self.plotlim[0]))
			if self.axisparms[3]=="linear" : y2=(self.height()-y-self.scrlim[1])/self.scrlim[3]*self.plotlim[3]+self.plotlim[1]
			else : y2=10.0**((self.height()-y-self.scrlim[1])/self.scrlim[3]*(log10(self.plotlim[3]+self.plotlim[1])-log10(self.plotlim[1]))+log10(self.plotlim[1]))
			return (x2,y2)
		except: return (0,0)
		
	def plot2scr(self,x,y) :
		""" converts plot coordinates to screen coordinates """
		try:
			if self.axisparms[2]=="linear" : x2=(x-self.plotlim[0])/self.plotlim[2]*self.scrlim[2]+self.scrlim[0]
			else : x2=(-(self.scrlim[2]*log(x)) + (self.scrlim[0] + self.scrlim[2])*log(10)*log10(self.plotlim[0])-self.scrlim[0]*log(10)*log10(self.plotlim[0] +self.plotlim[2])) /(log(10)*(log10(self.plotlim[0]) - log10(self.plotlim[0] + self.plotlim[2])))
			if self.axisparms[3]=="linear" :y2=(self.height()-y-self.plotlim[1])/self.plotlim[3]*self.scrlim[3]+self.scrlim[1]
			else : y2=(self.scrlim[3]*log(y) + self.height()*log(10.0)*log10(self.plotlim[1])-self.scrlim[1]*log(10.0)*log10(self.plotlim[1])-self.scrlim[3]*log(10.0)*log10(self.plotlim[1]) - self.height()*log(10.0)*log10(self.plotlim[1]+self.plotlim[3]) + self.scrlim[1]*log(10)*log10(self.plotlim[1]+self.plotlim[3])) / (log(10)*(log10(self.plotlim[1]) - log10(self.plotlim[1]+self.plotlim[3])))
			return (x2,y2)
		except: 
			return (0,0)

	def resize_event(self,width,height):
		self.needupd=1
		self.del_shapes(("xcross","ycross","lcross"))

	def setAxisParms(self,xlabel,ylabel,xlog="linear",ylog="linear"):
		if self.axisparms==(xlabel,ylabel,xlog,ylog): return
		self.axisparms=(xlabel,ylabel,xlog,ylog)
		self.needupd=1
		self.updateGL()
		
	def setAxes(self,key,xa,ya,za):
		if self.axes[key]==(xa,ya,za) : return
		self.axes[key]=(xa,ya,za)
		self.needupd=1
		self.updateGL()
		
	def setPlotParms(self,key,color,line,linetype,linewidth,sym,symtype,symsize):
		if self.pparm[key]==(color,line,linetype,linewidth,sym,symtype,symsize) : return
		self.pparm[key]=(color,line,linetype,linewidth,sym,symtype,symsize)
		self.needupd=1
		self.updateGL()
	
	def add_shape(self,k,s):
		"""Add a 'shape' object to be overlaid on the image. Each shape is
		keyed into a dictionary, so different types of shapes for different
		purposes may be simultaneously displayed. The 'scr' shapes are in
		screen coordinates rather than data coordinates
		
		0            1  2  3  4  5     6     7     8
		"rect"       R  G  B  x0 y0    x1    y1    linew
		"line"       R  G  B  x0 y0    x1    y1    linew
		"label"      R  G  B  x0 y0    text  size	linew
		"circle"     R  G  B  x0 y0    r     linew
		"scrrect"    R  G  B  x0 y0    x1    y1    linew
		"scrline"    R  G  B  x0 y0    x1    y1    linew
		"scrlabel"   R  G  B  x0 y0    text  size	linew
		"scrcircle"  R  G  B  x0 y0    r     linew
		"""
		self.shapes[k]=s
		self.shapechange=1
		self.updateGL()
	
	def add_shapes(self,d):
		self.shapes.update(d)
		self.shapechange=1
		self.updateGL()
	
	def del_shapes(self,k=None):
		if k:
			try:
				for i in k:
					if i in self.shapes : del self.shapes[i]
			except: 
				try: del self.shapes[k]
				except: return
		else:
			self.shapes={}
		self.shapechange=1
		self.updateGL()
	
	def keyPressEvent(self,event):
		# this event is being sent by the deskto
		pass
	
		
	def mousePressEvent(self, event):
		lc=self.scr2plot(event.x(),event.y())
		if event.button()==Qt.MidButton or (event.button()==Qt.LeftButton and event.modifiers()&Qt.AltModifier):
			self.show_inspector(1)
		elif event.button()==Qt.RightButton or (event.button()==Qt.LeftButton and event.modifiers()&Qt.AltModifier):
			self.del_shapes()
			self.rmousedrag=(event.x(),event.y())
		elif event.button()==Qt.LeftButton:
			self.add_shape("xcross",EMShape(("scrline",0,0,0,self.scrlim[0],self.height()-event.y(),self.scrlim[2]+self.scrlim[0],self.height()-event.y(),1)))
			self.add_shape("ycross",EMShape(("scrline",0,0,0,event.x(),self.scrlim[1],event.x(),self.scrlim[3]+self.scrlim[1],1)))
			self.add_shape("lcross",EMShape(("scrlabel",0,0,0,self.scrlim[2]-100,self.scrlim[3]-10,"%1.4g, %1.4g"%(lc[0],lc[1]),120.0,-1)))
			#if self.mmode==0:
				#self.emit(QtCore.SIGNAL("mousedown"), event)
				#return
			#elif self.mmode==1 :
				#try: 
					#del self.shapes["MEASL"]
				#except: pass
				#self.add_shape("MEAS",("line",.5,.1,.5,lc[0],lc[1],lc[0]+1,lc[1],2))
	
	def mouseMoveEvent(self, event):
		lc=self.scr2plot(event.x(),event.y())
		
		if  self.rmousedrag:
			self.add_shape("zoom",EMShape(("scrrect",0,0,0,self.rmousedrag[0],self.height()-self.rmousedrag[1],event.x(),self.height()-event.y(),1)))
		elif event.buttons()&Qt.LeftButton:
			self.add_shape("xcross",EMShape(("scrline",0,0,0,self.scrlim[0],self.height()-event.y(),self.scrlim[2]+self.scrlim[0],self.height()-event.y(),1)))
			self.add_shape("ycross",EMShape(("scrline",0,0,0,event.x(),self.scrlim[1],event.x(),self.scrlim[3]+self.scrlim[1],1)))
			self.add_shape("lcross",EMShape(("scrlabel",0,0,0,self.scrlim[2]-100,self.scrlim[3]-10,"%1.4g, %1.4g"%(lc[0],lc[1]),120.0,-1)))
#			self.add_shape("mcross",EMShape(("scrlabel",0,0,0,self.scrlim[2]-80,self.scrlim[3]-20,"%1.3g, %1.3g"%(self.plot2scr(*lc)[0],self.plot2scr(*lc)[1]),1.5,1)))
	
	def mouseReleaseEvent(self, event):
		lc =self.scr2plot(event.x(),event.y())
		if self.rmousedrag:
			lc2=self.scr2plot(*self.rmousedrag)
			if fabs(event.x()-self.rmousedrag[0])+fabs(event.y()-self.rmousedrag[1])<3 : self.limits=None
			else : self.limits=((min(lc[0],lc2[0]),max(lc[0],lc2[0])),(min(lc[1],lc2[1]),max(lc[1],lc2[1])))
			self.rmousedrag=None
			self.needupd=1
			self.del_shapes()  # also triggers an update
		#elif event.button()==Qt.LeftButton:
			#if self.mmode==0:
				#self.emit(QtCore.SIGNAL("mouseup"), event)
				#return
			#elif self.mmode==1 :
				#self.add_shape("MEAS",("line",.5,.1,.5,self.shapes["MEAS"][4],self.shapes["MEAS"][5],lc[0],lc[1],2))

	def wheelEvent(self, event):
		pass
		#if event.delta() > 0:
			#self.set_scale(self.scale + MAG_INC)	
		#elif event.delta() < 0:
			#if ( self.scale - MAG_INC > 0 ):
				#self.set_scale(self.scale - MAG_INC)
		## The self.scale variable is updated now, so just update with that
		#if self.inspector: self.inspector.set_scale(self.scale)

	def leaveEvent(self,event):
		pass

class EMPlot2DInspector(QtGui.QWidget):
	def get_desktop_hint(self):
		return "inspector"
	
	def __init__(self,target) :
		QtGui.QWidget.__init__(self,None)
		self.target=weakref.ref(target)
		vbl0=QtGui.QVBoxLayout(self)
		
		hbl = QtGui.QHBoxLayout()
		hbl.setMargin(2)
		hbl.setSpacing(6)
		hbl.setObjectName("hbl")
		
		# plot list
		self.setlist=QtGui.QListWidget(self)
		self.setlist.setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
		hbl.addWidget(self.setlist)
		
		vbl = QtGui.QVBoxLayout()
		vbl.setMargin(0)
		vbl.setSpacing(6)
		vbl.setObjectName("vbl")
		hbl.addLayout(vbl)
		
		self.color=QtGui.QComboBox(self)
		self.color.addItem("black")
		self.color.addItem("blue")
		self.color.addItem("red")
		self.color.addItem("green")
		vbl.addWidget(self.color)

		hbl2 = QtGui.QHBoxLayout()
		hbl2.setMargin(0)
		hbl2.setSpacing(6)
		vbl.addLayout(hbl2)
				
		# This is for line parms
		vbl2b = QtGui.QVBoxLayout()
		vbl2b.setMargin(0)
		vbl2b.setSpacing(6)
		hbl2.addLayout(vbl2b)
				
		self.lintog=QtGui.QPushButton(self)
		self.lintog.setText("Line")
		self.lintog.setCheckable(1)
		vbl2b.addWidget(self.lintog)
				
		self.linsel=QtGui.QComboBox(self)
		self.linsel.addItem("------")
		self.linsel.addItem("- - - -")
		self.linsel.addItem(".......")
		self.linsel.addItem("-.-.-.-")
		vbl2b.addWidget(self.linsel)
		
		self.linwid=QtGui.QSpinBox(self)
		self.linwid.setRange(1,10)
		vbl2b.addWidget(self.linwid)
		
		# This is for point parms
		vbl2a = QtGui.QVBoxLayout()
		vbl2a.setMargin(0)
		vbl2a.setSpacing(6)
		hbl2.addLayout(vbl2a)
				
		self.symtog=QtGui.QPushButton(self)
		self.symtog.setText("Symbol")
		self.symtog.setCheckable(1)
		vbl2a.addWidget(self.symtog)

		self.symsel=QtGui.QComboBox(self)
		self.symsel.addItem("circle")
		self.symsel.addItem("square")
		self.symsel.addItem("plus")
		self.symsel.addItem("triup")
		self.symsel.addItem("tridown")
		vbl2a.addWidget(self.symsel)
		
		self.symsize=QtGui.QSpinBox(self)
		self.symsize.setRange(0,25)
		vbl2a.addWidget(self.symsize)
		
		# per plot column selectors
		gl=QtGui.QGridLayout()
		gl.addWidget(QtGui.QLabel("X Col:",self),0,0,Qt.AlignRight)
		self.slidex=QtGui.QSpinBox(self)
		self.slidex.setRange(-1,1)
		gl.addWidget(self.slidex,0,1,Qt.AlignLeft)
		
		#self.slidex=ValSlider(self,(-1,1),"X col:",0)
		#self.slidex.setIntonly(1)
		#vbl.addWidget(self.slidex)
		
		gl.addWidget(QtGui.QLabel("Y Col:",self),1,0,Qt.AlignRight)
		self.slidey=QtGui.QSpinBox(self)
		self.slidey.setRange(-1,1)
		gl.addWidget(self.slidey,1,1,Qt.AlignLeft)
		#self.slidey=ValSlider(self,(-1,1),"Y col:",1)
		#self.slidey.setIntonly(1)
		#vbl.addWidget(self.slidey)
		
		gl.addWidget(QtGui.QLabel("C Col:",self),2,0,Qt.AlignRight)
		self.slidec=QtGui.QSpinBox(self)
		self.slidec.setRange(-1,1)
		gl.addWidget(self.slidec,2,1,Qt.AlignLeft)
		vbl.addLayout(gl)
		#self.slidec=ValSlider(self,(-1,1),"C col:",-1)
		#self.slidec.setIntonly(1)
		#vbl.addWidget(self.slidec)
		
		
		hbl2 = QtGui.QHBoxLayout()
		
		self.xlogtog=QtGui.QPushButton(self)
		self.xlogtog.setText("X Log")
		self.xlogtog.setCheckable(1)
		hbl2.addWidget(self.xlogtog)

		self.ylogtog=QtGui.QPushButton(self)
		self.ylogtog.setText("Y Log")
		self.ylogtog.setCheckable(1)
		hbl2.addWidget(self.ylogtog)
		
		vbl.addLayout(hbl2)

		vbl0.addLayout(hbl)
		
		hbl2 = QtGui.QHBoxLayout()	
		hbl2.addWidget(QtGui.QLabel("X Label:",self))
		self.xlabel=QtGui.QLineEdit(self)
		hbl2.addWidget(self.xlabel)
		vbl0.addLayout(hbl2)
		
		hbl2 = QtGui.QHBoxLayout()	
		hbl2.addWidget(QtGui.QLabel("Y Label:",self))
		self.ylabel=QtGui.QLineEdit(self)
		hbl2.addWidget(self.ylabel)
		vbl0.addLayout(hbl2)
		
	
#		self.setLayout(vbl0)

		self.quiet=0
		
		QtCore.QObject.connect(self.slidex, QtCore.SIGNAL("valueChanged(int)"), self.newCols)
		QtCore.QObject.connect(self.slidey, QtCore.SIGNAL("valueChanged(int)"), self.newCols)
		QtCore.QObject.connect(self.slidec, QtCore.SIGNAL("valueChanged(int)"), self.newCols)
		QtCore.QObject.connect(self.setlist,QtCore.SIGNAL("currentRowChanged(int)"),self.newSet)
		QtCore.QObject.connect(self.color,QtCore.SIGNAL("currentIndexChanged(QString)"),self.updPlot)
		QtCore.QObject.connect(self.symtog,QtCore.SIGNAL("clicked()"),self.updPlot)
		QtCore.QObject.connect(self.symsel,QtCore.SIGNAL("currentIndexChanged(QString)"),self.updPlot)
		QtCore.QObject.connect(self.symsize,QtCore.SIGNAL("valueChanged(int)"),self.updPlot)
		QtCore.QObject.connect(self.xlogtog,QtCore.SIGNAL("clicked()"),self.updPlot)
		QtCore.QObject.connect(self.ylogtog,QtCore.SIGNAL("clicked()"),self.updPlot)
		QtCore.QObject.connect(self.lintog,QtCore.SIGNAL("clicked()"),self.updPlot)
		QtCore.QObject.connect(self.linsel,QtCore.SIGNAL("currentIndexChanged(QString)"),self.updPlot)
		QtCore.QObject.connect(self.linwid,QtCore.SIGNAL("valueChanged(int)"),self.updPlot)
		QtCore.QObject.connect(self.xlabel,QtCore.SIGNAL("textChanged(QString)"),self.updPlot)
		QtCore.QObject.connect(self.ylabel,QtCore.SIGNAL("textChanged(QString)"),self.updPlot)
		self.datachange()
		
		
		#QtCore.QObject.connect(self.gammas, QtCore.SIGNAL("valueChanged"), self.newGamma)
		#QtCore.QObject.connect(self.invtog, QtCore.SIGNAL("toggled(bool)"), target.set_invert)
		#QtCore.QObject.connect(self.mmode, QtCore.SIGNAL("buttonClicked(int)"), target.set_mouse_mode)

	def updPlot(self,s=None):
		if self.quiet : return
		if self.xlogtog.isChecked() : xl="log"
		else : xl="linear"
		if self.ylogtog.isChecked() : yl="log"
		else : yl="linear"
		self.target().setAxisParms(self.xlabel.text(),self.ylabel.text(),xl,yl)
		self.target().setPlotParms(str(self.setlist.currentItem().text()),self.color.currentIndex(),self.lintog.isChecked(),
			self.linsel.currentIndex(),self.linwid.value(),self.symtog.isChecked(),self.symsel.currentIndex(),self.symsize.value())

	def newSet(self,row):
		self.quiet=1
		try:
			i=str(self.setlist.item(row).text())
		except: 
#			print "plot error"
			return
		self.slidex.setRange(-1,len(self.target().data[i])-1)
		self.slidey.setRange(-1,len(self.target().data[i])-1)
		self.slidec.setRange(-1,len(self.target().data[i])-1)
		self.slidex.setValue(self.target().axes[i][0])
		self.slidey.setValue(self.target().axes[i][1])
		self.slidec.setValue(self.target().axes[i][2])
		
		pp=self.target().pparm[i]
		self.color.setCurrentIndex(pp[0])
		
		self.lintog.setChecked(pp[1])
		self.linsel.setCurrentIndex(pp[2])
		self.linwid.setValue(pp[3])
		
		self.symtog.setChecked(pp[4])
		self.symsel.setCurrentIndex(pp[5])
		self.symsize.setValue(pp[6])
		self.quiet=0

	def newCols(self,val):
		if self.target: 
			self.target().setAxes(str(self.setlist.currentItem().text()),self.slidex.value(),self.slidey.value(),self.slidec.value())
	
	def datachange(self):
		
		self.setlist.clear()
		
		keys=self.target().data.keys()
		keys.sort()
		
		for i,j in enumerate(keys) :
			self.setlist.addItem(j)

		if len(keys) > 0 : self.setlist.setCurrentRow(0)
		
# This is just for testing, of course
if __name__ == '__main__':

	app = EMStandAloneApplication()
	window = EMPlot2DModule(app)
	if len(sys.argv)==1 : 
		l=[i/30.*pi for i in range(30)]
		window.set_data("test",[[1,2,3,4],[2,3,4,3]])
		window.set_data("test2",[l,[sin(2*i) for i in l]])
	else:
		for i in range(1,len(sys.argv)):
			window.set_data_from_file(sys.argv[i])
	
	app.show()
	app.execute()
