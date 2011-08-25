#!/usr/bin/env python

from PyQt4 import QtCore, QtGui, QtOpenGL
from emscene3d import EMScene3D, EMInspector3D, EMInspectorControlShape
from emshapeitem3d import *

from EMAN2 import *

class GLdemo(QtGui.QWidget):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		self.widget = EMScene3D()
		#self.widget.camera.useprespective(50, 0.5)
#		self.cube1 = glCube(50.0)
		self.cube1 = EMCube(50.0)
		self.widget.addChild(self.cube1)    # Something to Render something..... an EMItem3D
		#self.widget.activatenode(cube1)
#		self.cube2 = glCube(50.0)
		self.cube2 = EMCube(50.0)
		self.widget.addChild(self.cube2)
		#self.widget.activatenode(cube2)
		
		self.sphere = EMSphere(50.0)
		self.widget.addChild(self.sphere)
		
		self.cylinder = EMCylinder(50, 300)
		self.widget.addChild(self.cylinder)
		
		self.cone = EMCone(50, 300)
		self.widget.addChild(self.cone)
		
		self.line = EMLine(10,10,10,200,200,200, 16)
		self.widget.addChild(self.line)
		
		self.text1 = EM3DText('3D text in extrude', 75)
		self.widget.addChild(self.text1)
		
		self.text2 = EM3DText('3D text in texture', 75, FTGLFontMode.TEXTURE)
		self.widget.addChild(self.text2)
		
#		self.text3 = EM3DText('3D text in bitmap', 75, FTGLFontMode.BITMAP)
#		self.widget.addChild(self.text3)
		
		self.text4 = EM3DText('3D text in polygon', 75, FTGLFontMode.POLYGON)
		self.widget.addChild(self.text4)
		
		self.text5 = EM3DText('3D text in outline', 75, FTGLFontMode.OUTLINE)
		self.widget.addChild(self.text5)
		
		self.text6 = EM3DText('3D text in pixmap', 75, FTGLFontMode.PIXMAP)
		self.widget.addChild(self.text6)
		
		#Show inspector
		self.widget.showInspector()
		
		# QT stuff to display the widget
		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(self.widget)
		self.setLayout(vbox)
		self.setGeometry(300, 300, 600, 600)
		self.setWindowTitle('BCM EM Viewer')
	
	def show_inspector(self):
		self.inspector.show()
		
if __name__ == "__main__":
	import sys
	app = QtGui.QApplication(sys.argv)
	window = GLdemo()
	window.show()
	app.exec_()
	