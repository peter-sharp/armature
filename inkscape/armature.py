#!/usr/bin/env python

import inkex
import xml
import os
import gettext
_ = gettext.gettext
from simplestyle import *
from gi.repository import Gtk

#styles
ArmatureTitleStyle = { 'font-family' : 'arial', 'font-size' : '24pt' } #'text-align' : 'center', 'text-anchor' : 'middle',
ArmatureSubTitleStyle = { 'font-family' : 'arial', 'font-size' : '18pt','font-style':'italic' }
ArmatureRowLabelStyle = {'font-size': '16pt', 'font-weight' : 'bold'}
ArmatureBold = {'font-weight':'bold'}

def readToEnd(fileName):
	stream = open(fileName ,"r")
	data = stream.read()
	stream.close()
	return data

class UiEventHandler:
	def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

    def onApply(self, button):
        return True

class Armature(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		#namespaces
		#inkex.NSS[u'armature']=u'https://github.com/brianbv/armature'
		#members
		self.svg = None
		self.armatureLayer = None
		self.width=0
		self.height=0

		#options
		self.OptionParser.add_option("",   "--active-tab", action="store", type="string", dest="active_tab", default="",	help="Defines which tab is active")
		self.OptionParser.add_option("",   "--newLayerSet", action="store", type="string", dest="newLayerSet", default="",	help="Creates new layer set.")
		self.OptionParser.add_option("",   "--activeLayerSet", action="store", type="string", dest="activeLayerSet", default="",	help="Sets active layer set.")

		self.OptionParser.add_option("",   "--wireframesTitle", action="store", type="string", dest="wireframesTitle", default="",	help="Sets the title of the page.")
		self.OptionParser.add_option("",   "--fileName", action="store", type="string", dest="fileName", default="",	help="Filename to be generated.")
	def effect(self):

		#why does active_tab have quotes? Who knows.
		self.activeTab =  str(self.options.active_tab).replace('"','')
		if self.activeTab=='createLayerSetPage':
			self.startRenderingSvgUi()
		elif self.activeTab=='generateWireframes':
			self.generateWireframes()
		elif not(self.options.activeLayerSet is None):
			layerSetId=self.options.activeLayerSet

			dataNode = self.getElementById('ArmatureDataNode-%s' % layerSetId )

			if (dataNode is None):
				inkex.errormsg('Layerset %s does not exist.' % layerSetId)
			else:
				layerStates=parseStyle( dataNode.get( inkex.addNS('label', 'inkscape')) )
				self.toggleLayers(layerStates['on'].split(','),True)
				self.toggleLayers(layerStates['off'].split(','),False)

		else:
			inkex.errormsg('Please enter a layerset name to select.')


	#effect specific implementation
	def toggleLayers(self, layers, state):
		display='inline'
		if not state: display='none'
		for layer in layers:
			el=self.getElementById( layer.strip())

			if (not el is None):
				style=parseStyle( el.get('style') )
				style['display'] = display
				el.set('style',formatStyle(style))

	#render SVG UI
	def startRenderingSvgUi(self):
		self.cursorY = 310
		self.svg = self.document.getroot()
		self.width= self.unittouu(self.svg.get('width'))
		self.height= self.unittouu(self.svg.get('height'))

		#draw the UI and create layers, if it's not been done yet
		self.renderArmatureUI()

		if not self.options.newLayerSet is None:
			#find out what the state of the layers are
			layerInfo=self.getLayerInfo()
			self.updateArmatureData(self.options.newLayerSet,layerInfo)
		else:
			inkex.errormsg("Enter a title to update an existing set, or create a new one.")

	def getLayerInfo(self):
		result=""
		layers=self.svg.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
		armatureLayerInfo = { 'on' : [], 'off' : []}

		for layer in layers:
			id = layer.get('id')
			className= layer.get('class')

			#ignore internal layers used for UI and data
			if (not className=='armature-internal'):
				layer.set('id', layer.get(inkex.addNS('label', 'inkscape')).replace(' ',''))
				layerStyle = parseStyle( layer.get('style') )

				if ('display' in layerStyle and layerStyle['display']=='none'):
					armatureLayerInfo['off'].append( layer.get('id') )
				else:
					armatureLayerInfo['on'].append( layer.get('id') )

		return armatureLayerInfo

	#updates an existing row, if one does not exist, one is created
	def updateArmatureData(self,layerSetName,layerGroup):
		stuff = ""
		layerSetId = layerSetName.replace(' ','')

		#has a data node been created
		query='//*[@class="data-node %s"]' % layerSetId
		nodes=self.armatureLayer.xpath(query)

		if not nodes is None and len(nodes)>0:
		#find the node, and update it

			for n in nodes:
				currentData = parseStyle( n.get( inkex.addNS('label', 'inkscape') ) )
				if 'state' in currentData and currentData['state']=='on':
					currentData['on']=layerGroup['on']
				else:
					currentData['off']=layerGroup=['off']

				n.set(inkex.addNS('label', 'inkscape'), formatStyle(currentData) )
		else:
			yNodes=self.armatureLayer.xpath('//*[@y]')
			maxY=0
			for yNode in yNodes:
				className = yNode.get('class')
				if not className is None and 'data-node' in className:
					newY = float(yNode.get('y'))
					if newY>maxY: maxY=newY

			if maxY>self.cursorY: self.cursorY = maxY
			self.cursorY+=35
			self.renderArmatureData(layerSetId,layerGroup)


		#inkex.errormsg(stuff)
	#create new armature
	def renderArmatureData(self,layerSetId,layerGroup):
		title = inkex.etree.SubElement(self.armatureLayer,'text')
		title.set('style', formatStyle(ArmatureRowLabelStyle))
		title.set('x', '20' )
		title.set('y', str(self.cursorY))
		title.set('class','data-node')
		title.set('id', 'ArmatureDataNode-%s' % layerSetId)
		 # title.get('height')
		title.text=layerSetId
		style ={'set':layerSetId, 'on': ','.join(layerGroup['on']), 'off' : ','.join(layerGroup['off'])}
		title.set( inkex.addNS('label', 'inkscape'), formatStyle( style ) )

		self.cursorY+=20


	def renderArmatureUI(self):
		armatureContainer = self.getElementById('ArmatureInfo')
		if armatureContainer is None:
			#main container
			curY=50
			armatureContainer = inkex.etree.SubElement(self.svg, 'g')

			armatureContainer.set('id','ArmatureInfo')
			armatureContainer.set(inkex.addNS('label', 'inkscape'), 'Armature')
			armatureContainer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
			armatureContainer.set('class','armature-internal')

			armatureUI = inkex.etree.SubElement(armatureContainer, 'g')
			armatureUI.set(inkex.addNS('label', 'inkscape'), 'Armature UI')
			#armatureUI.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
			armatureUI.set('id','ArmatureUI')
			armatureUI.set('class','armature-internal')
			armatureUI.set( inkex.addNS('insensitive','sodipodi'),'true')

			#TODO: could look into loading an SVG file for this UI
			bg = inkex.etree.SubElement(armatureUI, 'rect')
			bg.set('width',str(self.width))
			bg.set('height',str(self.height))
			bg.set('fill','#FFFFFF')
			bg.set('x','0')
			bg.set('y','0')

			uiData= open('armature.ui.svg',"r").read()
			armatureUI.append(  inkex.etree.fromstring(uiData))

			self.armatureLayer = inkex.etree.SubElement(armatureContainer, 'g')
			self.armatureLayer.set(inkex.addNS('label', 'inkscape'), 'Armature Data')
			self.armatureLayer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
			self.armatureLayer.set('id','ArmatureData')
			self.armatureLayer.set('y', '0' )
			self.armatureLayer.set('class','armature-internal')

		else:
			self.armatureLayer = self.getElementById('ArmatureData')

	def generateWireframes(self):
		""" generates wire-frames from given layer-sets and outputs them into a single html file with javascript controls"""
		#read HTML file
		svg = self.document.getroot()

		htmlData = readToEnd(os.path.join('armature','armature.html'))
		jsData =  readToEnd( os.path.join('armature','armature.js'))

		dirName = os.path.dirname(self.svg_file)
		outfile =  os.path.join(dirName, self.options.fileName)
		stream =  open(outfile,"w");

		htmlData = htmlData.replace('{#wireframesTitle}','Armature Wireframes HTML wrapper') \
						.replace('{#armatureJs}',jsData) \
						.replace('{#svg}',inkex.etree.tostring(svg) ) \

		stream.write( htmlData )
		stream.close()
		inkex.errormsg('Wireframes generated.  You can find them here: \n %s' % outfile  )

if __name__ == '__main__':
  e = Armature()
  e.affect()
