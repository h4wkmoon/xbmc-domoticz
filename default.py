import xbmc, xbmcgui,xbmcaddon

import urllib2
if sys.version_info < (2, 7):
	import simplejson
else:
	import json as simplejson
	

### get addon info and set globals
__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')
__author__       = __addon__.getAddonInfo('author')
__version__      = __addon__.getAddonInfo('version')
__addonpath__    = __addon__.getAddonInfo('path')
__localize__     = __addon__.getLocalizedString
__user__=__addon__.getSetting('login')
__password__=__addon__.getSetting('password')
__rooturl__=__addon__.getSetting('url')
__favonly__=__addon__.getSetting('favonly')

while __rooturl__=='': 
	__addon__.openSettings()
	__user__=__addon__.getSetting('login')
	__password__=__addon__.getSetting('password')
	__rooturl__=__addon__.getSetting('url')
	__favonly__=__addon__.getSetting('favonly')




# Log function. based on XBMC standard
def log( text, severity=xbmc.LOGNOTICE ):
	if type( text).__name__=='unicode':
		text = text.encode('utf-8')
	message = ('[%s] - %s' % ( __addonname__ ,text.__str__() ) )
	xbmc.log( msg=message, level=severity)

# Popup function. based on XBMC standard
def message( message):
		dialog = xbmcgui.Dialog()
		dialog.ok("My message title", message)
 

# Manage authentication
if __user__!='': 		# Authentication optional
	passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, __rooturl__, __user__, __password__)
	authhandler = urllib2.HTTPBasicAuthHandler(passman)
	opener = urllib2.build_opener(authhandler)
	urllib2.install_opener(opener)

#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92


# Dict used for internalization
# The keys are Domoticz status, the values are lablels form the international string.xml files.
__labels__ = {	'off':30040,
			'on' : 30041,
			'open' : 30042,
			'closed' : 30043,
			'panic': 30044,
			'normal' : 30045 }

# When a switch is XX, we can switch it to YY
__opposite_status__ = {'Off':'On',
					'On':'Off',
					'Closed':'Open',
					'Open':'Closed',
					'Panic':'Normal',
					'Normal':'Panic'}
					
 
# Ugly thing. This lists the custom image available by type of item.
# As Domoticz has several attributes to identify the item types, this ulgy thing stays, for now.
__customimages__ = { 'lightbulb': ['lightbulb','wallsocket','tv','harddisk','printer','amplifier','computer','fan','speaker','generic','push'],
						'smoke': ['smoke'],
						'contact': ['contact'],
						'blinds': ['blinds'],
						'temperature':['temperature'],
						'siren': ['siren'],
						'dimmer':['dimmer'],
						'motion': ['motion'],
						'door': ['door'],
						'dusk': ['dusk']
						}


# Function to send commands to domoticz.
# It handles
# switches
# dimmer
# scenes & groups
def sendcmd(switchid,itemtype,cmd,level=0):
		log("Sending "+cmd+" to Switch "+str(switchid), xbmc.LOGNOTICE)
		thisurl=__rooturl__+"/json.htm?type=command&param="+itemtype+"&idx="+str(switchid)+"&switchcmd="+cmd+"&level="+str(level)
		log ("URL is "+thisurl , xbmc.LOGNOTICE)
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )
		try:
			pagehandle = urllib2.urlopen(thisurl)
			html = pagehandle.read()
			pagehandle.close()
		except:
			html="Error !!"
		xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		log(html, xbmc.LOGNOTICE)
		xbmc.sleep(2)

# This is how we interact with the dimmer
class Domoticzpopupslider(xbmcgui.WindowDialog):
	width=500
	height=200
	x=100
	y=100
	
	def __init__(self, *args, **kwargs):
		#and define it as self
		self.title=args[0]['title']
		self.level=args[0]['level']
		self.idx=args[0]['idx']
		log('running __init__ from Domoticzpopupslider class', xbmc.LOGNOTICE)
		
		self.fond=xbmcgui.ControlImage(self.x,self.y,self.width,self.height,"speedfan-panel.png",2)
		self.slider = xbmcgui.ControlSlider(self.x+int((self.width-9*self.width/10)/2),self.y+int((self.height-10)/2),int(9*self.width/10),10)
		self.title= xbmcgui.ControlLabel(self.x+int((self.width-9*self.width/10)/2),self.y+10,int(9*self.width/10),10,self.title)
		#~ log(self.title)
		self.addControl(self.fond)
		self.addControl(self.title)
		self.addControl(self.slider)
		self.slider.setPercent(int(self.level))
		self.setFocus(self.slider)
		
		
	def onInit(self):
		#tell the object to go read the log file, parse it, and put it into listitems for the XML
		log('running inInit from Domoticzpopupslider class', xbmc.LOGNOTICE)
        
        
# When the user goes back, the command to dimmer is sent, and the window is closed.
# Level is defined like that : 
# 0 = 0%
# 16 = 100%
	def onAction(self, action):
		#~ captures user input and acts as needed
		if(action == ACTION_PREVIOUS_MENU or action == ACTION_BACK):
			#if the user hits back or exit, close the window
			log('user initiated previous menu or back', xbmc.LOGNOTICE)
			global __windowopen__
			#set this to false so the worker thread knows the window is being closed
			__windowopen__ = False
			log('set windowopen to false', xbmc.LOGNOTICE)
			#tell the window to close
			log('tell the window to close', xbmc.LOGNOTICE)
			sendcmd(self.idx,'switchlight','Set%20Level',int(16*self.slider.getPercent()/100))
			self.close()
			


class DomoticzWindow(xbmcgui.WindowXMLDialog):

	def __init__(self, *args, **kwargs):

		#and define it as self
		log('running __init__ from DomoticzWindow class', xbmc.LOGNOTICE)

       
      
       
# INIT Function       
	def onInit(self):
		#tell the object to go read the log file, parse it, and put it into listitems for the XML
		log('running inInit from DomoticzWindow class', xbmc.LOGNOTICE)
		self.populateFromDomo()
        
	
     # When we click on an item, if it's a switch, a scene or a group, we switch it, 
     # if it's a dimmer, let's make the popup appear
     # And then regenerate the window.
	def onClick(self, control):
		item = self.getControl(control).getSelectedItem()
		log("Click  "+item.getProperty('isswitch'),xbmc.LOGNOTICE)
		if item.getProperty('type') == 'switchscene' or item.getProperty('type') == 'switchlight':
			sendcmd(int(item.getProperty('idx')),item.getProperty('type'),__opposite_status__[item.getProperty('data')],0)

		else:
			args={'title':item.getLabel(), 'idx':item.getProperty('idx'),'level':item.getProperty('level')}
			mydisplay = Domoticzpopupslider(args)
			mydisplay.doModal()
			del mydisplay
		
		self.populateFromDomo()

# Closes the windows.
	def onAction(self, action):
		#~ captures user input and acts as needed
		log('running onAction from DomoticzWindow class', xbmc.LOGNOTICE)
		if(action == ACTION_PREVIOUS_MENU or action == ACTION_BACK):
			#if the user hits back or exit, close the window
			log('user initiated previous menu or back', xbmc.LOGNOTICE)
			global __windowopen__
			#set this to false so the worker thread knows the window is being closed
			__windowopen__ = False
			log('set windowopen to false', xbmc.LOGNOTICE)
			#tell the window to close
			log('tell the window to close', xbmc.LOGNOTICE)
			self.close()


# The big thing.
	def populateFromDomo(self):
		results=self.getData()			# Ask domoticz for data
		self.getControl(120).reset()	# Reset the window. Used for update
		
		# A title
		item = xbmcgui.ListItem(label="XBMC Domoticz")			
		item.setProperty('istitle','true')
		self.getControl(120).addItem(item)
		
		odd=True	# Used to alernate the line colors.
		for myitem in results[u'result']:
			
			# If the user choose to display only the favoraites, then so be it.
			if __favonly__=="true" and  myitem[u'Favorite']==0:  
				continue
	
			# Groups & Scenes lack some attributes. Let's set the missing ones.
			if myitem[u'Type'] == 'Group' or myitem[u'Type'] == 'Scene':
				myitem[u'Data'] = myitem[u'Status']
				myitem[u'CustomImage'] = 10

			log("Adding"+myitem[u'Name'],xbmc.LOGNOTICE)

			# Ulgy thing because Domoticz does not handle Dusk sensors like the others
			# So I override the TypeImg.
			if u'SwitchType' in myitem and myitem[u'SwitchType'] == "Dusk Sensor":
				myitem[u'TypeImg']='dusk'


			# Choosing the right icon.
			# For 'lightbulb','blinds','contact','smoke','siren','motion','door' and 'dusk' items, i choose the customImage, suffixed with the status (on/off). 
			if myitem[u'TypeImg']  in ['lightbulb','blinds','contact','smoke','siren','motion','door','dusk']:
				log(myitem[u'CustomImage'])
				mytype=__customimages__[myitem[u'TypeImg']][myitem[u'CustomImage']]+"-"+myitem[u'Status'].lower()+".png"
			# For Temperature, I choose the one that matches the range
			elif myitem[u'TypeImg'] == "temperature":
				mini=int(float(myitem[u'Data'].split(',')[0].split(' ')[0])/5)*5
				maxi=mini+5
				mytype="temp-"+str(mini)+"-"+str(maxi)+".png"
			# For dimmer, I choose between on and off by comparing the level with 50%.
			# And still, we allow the use of custom images.
			elif myitem[u'TypeImg'] == 'dimmer':
				status="on"
				if myitem[u'Level']<50:
					status='off'
				mytype=__customimages__[myitem[u'TypeImg']][myitem[u'CustomImage']]+"-"+status+".png"
			else:
				mytype=myitem[u'TypeImg'].lower()+".png"

			# There we translate Domoticz lables using the standard functionds of xbmc
			if myitem[u'Data'].lower() in __labels__:
				myitem[u'Data']=__localize__(__labels__[myitem[u'Data'].lower()])
              
            # Adding the item, one line is grey, the next is black.  
			item = xbmcgui.ListItem(label=myitem[u'Name'],label2=myitem[u'Data'])
			item.setProperty('idx',myitem[u'idx'])
			odd= not odd
			if odd:
				item.setProperty('isodd','true')
			else:
				item.setProperty('isodd','false')

			# Setting the property "type", used to know how the programm will interact with it.
			if myitem[u'Type'] in ['Lighting 2','Lighting 1','Lighting 4','Security']:
				if myitem[u'TypeImg']=='dimmer':
					item.setProperty('type','dimmer')
				else:
					item.setProperty('type','switchlight')
			elif myitem[u'Type'] in ['Scene','Group']:
				item.setProperty('type','switchscene')
			else:
				item.setProperty('type','none')
			
			# Data will be used when we click on the item.
			if u'Status' in myitem:
				item.setProperty('data',myitem[u'Status'])
			
			# Level will be used by the slider popup.
			if u'Level' in myitem:
				item.setProperty('level',str(myitem[u'Level']))

			# Set the icon
			item.setIconImage(mytype)
			
			self.getControl(120).addItem(item)
			

	def getData(self):
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        
		url=__rooturl__+u'/json.htm?type=devices&filter=all&used=true&order=Name'

		log('URL is '+url,xbmc.LOGNOTICE)
        
        
		try:
			pagehandle = urllib2.urlopen(url)
			#~ pagehandle = open('/home/fpege/json.html', 'r')
			html = pagehandle.read()
			pagehandle.close()
		except urllib2.HTTPError, e:
			log('HTTPError = ' + str(e.code))
			message('HTTPError = ' + __localize__(int("30"+str(e.code))))
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except urllib2.URLError, e:
			log('URLError = ' + str(e.reason))
			message('URLError = ' +  __localize__(30404))
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except httplib.HTTPException, e:
			log('HTTPException')
			message('HTTPException')
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except Exception:
			import traceback
			log('generic exception: ' + traceback.format_exc())
			message('generic exception: ' + traceback.format_exc())
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""

			

		xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		return simplejson.loads(html)
 
 


w = DomoticzWindow("domoticz.xml", __addonpath__, "Default")
w.doModal()
del w
