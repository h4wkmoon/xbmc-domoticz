import xbmc, xbmcgui,xbmcaddon
from threading import Thread
import time
import datetime

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
__images__		 = __addonpath__+'/resources/skins/Default/media/'
__localize__     = __addon__.getLocalizedString
__user__=__addon__.getSetting('login')
__password__=__addon__.getSetting('password')
__rooturl__=__addon__.getSetting('url')
__favonly__=__addon__.getSetting('favonly')
DEBUG = __addon__.getSetting('debug')
__view__=int(__addon__.getSetting('view'))

while __rooturl__=='': 
	__addon__.openSettings()
	__user__=__addon__.getSetting('login')
	__password__=__addon__.getSetting('password')
	__rooturl__=__addon__.getSetting('url')
	__favonly__=__addon__.getSetting('favonly')

__windowopen__=None

VIEW_LIST=0
VIEW_WIDGET=1

# Log function. based on XBMC standard
def log( text, severity=xbmc.LOGNOTICE ):
	if type( text).__name__=='unicode':
		text = text.encode('utf-8')
	message = ('[%s] - %s' % ( __addonname__ ,text.__str__() ) )
	if severity == xbmc.LOGDEBUG or DEBUG=="true":
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
ACTION_MOVE_LEFT=1
ACTION_MOVE_RIGHT=2
ACTION_SELECT_ITEM=[100,7,12]
ACTION_ENTER=135
ACTION_CONTEXT_MENU = [ 117, 101 ]


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
def sendcmd(args):
		opt=""
		for val in args:
			if opt!="":
				opt=opt+"&"
			opt=opt+val+"="+args[val]
		#http://www.bbrose.net/domoticz//json.htm?cmd=On&type=command&param=switchlight&idx=22

		#~ log("Sending "+cmd+" to Switch "+str(switchid), xbmc.LOGNOTICE)
		#~ thisurl=__rooturl__+"/json.htm?type=command&param="+itemtype+"&idx="+str(switchid)+"&switchcmd="+cmd+"&level="+str(level)
		thisurl=__rooturl__+"/json.htm?"+opt
		log ("URL is "+thisurl , xbmc.LOGNOTICE)
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )
		try:
			pagehandle = urllib2.urlopen(thisurl)
			html = pagehandle.read()
			pagehandle.close()
		except:
			html="Error !!"
		xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		log(html, xbmc.LOGERROR)
		xbmc.sleep(2)
		
def getData():
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        
		url=__rooturl__+u'/json.htm?type=devices&filter=all&used=true&order=Name'

		log('URL is '+url,xbmc.LOGNOTICE)
        
        
		try:
			pagehandle = urllib2.urlopen(url)
			html = pagehandle.read()
			pagehandle.close()
		except urllib2.HTTPError, e:
			log('HTTPError = ' + str(e.code) ,xbmc.LOGERROR)
			message('HTTPError = ' + __localize__(int("30"+str(e.code))))
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except urllib2.URLError, e:
			log('URLError = ' + str(e.reason),xbmc.LOGERROR)
			message('URLError = ' +  __localize__(30404))
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except httplib.HTTPException, e:
			log('HTTPException',xbmc.LOGERROR)
			message('HTTPException')
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""
		except Exception:
			import traceback
			log('generic exception: ' + traceback.format_exc(),xbmc.LOGERROR)
			message('generic exception: ' + traceback.format_exc())
			xbmc.executebuiltin( "Dialog.Close(busydialog)" )
			self.onAction(ACTION_BACK)
			return ""

			
		xbmc.executebuiltin( "Dialog.Close(busydialog)" )
		return simplejson.loads(html)
		
def transformDomoticz(json):
	results=[]
	for myitem in json[u'result']:
		item={}
		# If the user choose to display only the favoraites, then so be it.
		if __favonly__=="true" and  myitem[u'Favorite']==0:  
			continue
			
		if myitem[u'Type'] == 'Group' or myitem[u'Type'] == 'Scene':
				item[u'Data'] = myitem[u'Status']
				item[u'CustomImage'] = 10
		else:
				item[u'Data'] = myitem['Data']
				item[u'CustomImage']=myitem[u'CustomImage']
				
		# There we translate Domoticz lables using the standard functionds of xbmc
		if item[u'Data'].lower() in __labels__:
			item[u'Data']=__localize__(__labels__[item[u'Data'].lower()])
		
		# Domoticz handles dusk sensors wierdly, in my opinion.
		if u'SwitchType' in myitem and myitem[u'SwitchType'] == "Dusk Sensor":
				item[u'TypeImg']='dusk'
		else:
				item[u'TypeImg']= myitem[u'TypeImg']
	
		# Choose the icon
		if myitem[u'TypeImg']  in ['lightbulb','blinds','contact','smoke','siren','motion','door','dusk']:
			log("CustomImage :" + str(item[u'CustomImage']),xbmc.LOGDEBUG)
			icon=__customimages__[myitem[u'TypeImg']][item[u'CustomImage']]+"-"+myitem[u'Status'].lower()+".png"
			# For Temperature, I choose the one that matches the range
		elif myitem[u'TypeImg'] == "temperature":
			mini=int(float(myitem[u'Data'].split(',')[0].split(' ')[0])/5)*5
			if mini < 0:
				icon="ice.png"
			else:
				maxi=mini+5
				icon="temp-"+str(mini)+"-"+str(maxi)+".png"

		# For dimmer, I choose between on and off by comparing the level with 50%.
		# And still, we allow the use of custom images.
		elif myitem[u'TypeImg'] == 'dimmer':
			status="on"
			if myitem[u'Level']<50:
				status='off'
			icon=__customimages__[myitem[u'TypeImg']][myitem[u'CustomImage']]+"-"+status+".png"
		else:
			icon=myitem[u'TypeImg'].lower()+".png"
		
		item[u'Icon']=icon
		
		# Setting the property "type", used to know how the programm will interact with it.
		if myitem[u'Type'] in ['Lighting 2','Lighting 1','Lighting 4','Security']:
			if myitem[u'TypeImg']=='dimmer':
				mytype='dimmer'
			elif myitem[u'TypeImg']=='blinds':
				mytype='blinds'
			else:
				mytype='switchlight'
		elif myitem[u'Type'] in ['Scene','Group']:
			mytype='switchscene'
		else:
			mytype='none'
		log(myitem[u'Name']+item[u'Icon']+myitem[u'Type'])

		
		item[u'Type'] = mytype
		log(myitem[u'Name']+item[u'Icon']+item[u'Type'])

		item[u'Idx'] = myitem[u'idx']
		item[u'Name'] = myitem[u'Name']
		if 'Status' in myitem:
			item[u'Status'] = myitem[u'Status']
		log(myitem[u'Name']+item[u'Icon']+myitem[u'Type'])
		
		item[u'Favorite']=myitem[u'Favorite']
		
		if 'Level' in myitem:
			item[u'Level'] = myitem[u'Level']
		
		results.append(item)
		
	return results

# Almost completely copied from speedfan.
def updateWindow(name, w):
    #this is the worker thread that updates the window information every w seconds
    #this strange looping exists because I didn't want to sleep the thread for very long
    #as time.sleep() keeps user input from being acted upon
    log('running the worker thread from inside the def',xbmc.LOGNOTICE);
    while __windowopen__ and (not xbmc.abortRequested):
        #start counting up to the delay set in the preference and sleep for one second
        log('start counting the delay set in the preference',xbmc.LOGNOTICE);
        for i in range(int(__addon__.getSetting('update_delay'))):
            #as long as the window is open, keep sleeping
            if __windowopen__:
                log('window is still open, sleep 1 second',xbmc.LOGNOTICE);
                time.sleep(1)
                #~ xbmc.sleep(1000)
            #otherwise drop out of the loop so we can exit the thread
            else:
                break
        #as long as the window is open grab new data and refresh the window
        if __windowopen__:
            log('window is still open, updating the window with new data',xbmc.LOGNOTICE);
            w.populateFromDomo()



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
		self.fond=xbmcgui.ControlImage(self.x,self.y,self.width,self.height,__images__+"speedfan-panel.png",2)
		self.slider = xbmcgui.ControlSlider(self.x+int((self.width-9*self.width/10)/2),self.y+int((self.height-10)/2),int(9*self.width/10),10)  #,texturefocus=os.path.join(__addonpath__,'resources','skins','Default','media','slider-images-handle.png'),texture=os.path.join(__addonpath__,'resources','skins','Default','media','slider-images-handle.png'))
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
			#tell the window to close
			log('tell the window to close', xbmc.LOGNOTICE)
			myargs={'idx':str(self.idx),
					'type':'command',
					'param':'switchlight',
					'switchcmd':'Set%20Level',
					'level':str(int(16*self.slider.getPercent()/100))
					}
			sendcmd(myargs)
			self.close()
			

class DomoticzContext(xbmcgui.WindowDialog):
	width=500
	height=200
	x=100
	y=100
	line_height=50
	
	def __init__(self, *args, **kwargs):
		#and define it as self
		self.idx=args[0]['idx']
		self.fav=args[0]['fav']
		self.title=args[0]['title']
		self.itemtype=args[0]['type']
		self.fond=xbmcgui.ControlImage(self.x,self.y,self.width,self.height,__images__+"speedfan-panel.png")
		self.title= xbmcgui.ControlLabel(self.x+int((self.width-9*self.width/10)/2),self.y+10,int(9*self.width/10),10,self.title)
		if self.fav>0:
			text=__localize__(30071)
		else:
			text=__localize__(30070)
		self.setfav=xbmcgui.ControlButton(self.x+int((self.width-9*self.width/10)/2),
												self.y+10+self.line_height,
												int(9*self.width/10),
												self.line_height,
												label=text)
		
		log(text)

		self.addControl(self.fond)
		self.addControl(self.title)
		self.addControl(self.setfav)
		self.actions={}
		self.actions[self.setfav.getId()]='self.dosetfav()'
		
	def dosetfav(self):
		if self.itemtype=='switchscene':
			favcmd='makescenefavorite'
		else:
			favcmd='makefavorite'
		if self.fav>0:
			isfav="0"
		else:
			isfav="1"
		myargs={'idx':self.idx,
					'type':'command',
					'param':favcmd,
					'isfavorite':isfav
					}
		sendcmd(myargs)
		self.close()
		
	def Click(self,control):
		eval(self.actions[control])

	def onAction(self, action):
		log('running onAction from DomoticzContext class. Action:'+str(action.getId()), xbmc.LOGNOTICE)
		#~ captures user input and acts as needed
		if(action == ACTION_PREVIOUS_MENU or action == ACTION_BACK):
			#if the user hits back or exit, close the window
			log('user initiated previous menu or back', xbmc.LOGNOTICE)
			#tell the window to close
			log('tell the  Domoticzpopupblinds window to close', xbmc.LOGNOTICE)
			self.close()
		elif action.getId() in ACTION_SELECT_ITEM:
			self.Click(self.getFocusId())
			
class Domoticzpopupblinds(xbmcgui.WindowDialog):
	width=500
	height=200
	x=100
	y=100
	
	def __init__(self, *args, **kwargs):
		#and define it as self
		self.title=args[0]['title']
		self.idx=args[0]['idx']
		log('running __init__ from Domoticzpopupblinds class', xbmc.LOGNOTICE)
		self.fond=xbmcgui.ControlImage(self.x,self.y,self.width,self.height,__images__+"speedfan-panel.png",2)
		self.on=xbmcgui.ControlButton(self.x+int(self.width/3),self.y+self.height-100,48,48,focusTexture=__images__+"blinds-open.png",noFocusTexture=__images__+"blinds-open-nofocus.png",label="On")
		self.off=xbmcgui.ControlButton(self.x+int(2*self.width/3),self.y+self.height-100,48,48,focusTexture=__images__+"blinds-closed.png",noFocusTexture=__images__+"blinds-closed-nofocus.png",label="Off")
		self.title= xbmcgui.ControlLabel(self.x+int((self.width-9*self.width/10)/2),self.y+10,int(9*self.width/10),10,self.title)
		#~ log(self.title)
		self.addControl(self.fond)
		self.addControl(self.title)
		self.addControl(self.on)
		self.addControl(self.off)
		self.setFocus(self.on)
		self.on.setEnabled(True)
		self.off.setEnabled(True)
		
	def onInit(self):
		#tell the object to go read the log file, parse it, and put it into listitems for the XML
		log('running inInit from Domoticzpopupblinds class', xbmc.LOGDEBUG)
		
	def onInit(self):
		#tell the object to go read the log file, parse it, and put it into listitems for the XML
		log('running inInit from Domoticzpopupblinds class', xbmc.LOGDEBUG)

	def onClick(self, control):
		log('running onClick from Domoticzpopupblinds class', xbmc.LOGNOTICE)
		log("Click blinds"+str(control), xbmc.LOGNOTICE)
		if control==self.on.getId():
			log("ON", xbmc.LOGNOTICE)
			myargs={'idx':str(self.idx),
					'type':'command',
					'param':'switchlight',
					'switchcmd':'On'
					}
			sendcmd(myargs)
		elif control==self.off.getId():
			log("OFF", xbmc.LOGNOTICE)
			myargs={'idx':str(self.idx),
					'type':'command',
					'param':'switchlight',
					'switchcmd':'Off'
					}
			sendcmd(myargs)

	def onAction(self, action):
		log('running onAction from Domoticzpopupblinds class. Action:'+str(action.getId()), xbmc.LOGNOTICE)
		#~ captures user input and acts as needed
		if(action == ACTION_PREVIOUS_MENU or action == ACTION_BACK):
			#if the user hits back or exit, close the window
			log('user initiated previous menu or back', xbmc.LOGNOTICE)
			#tell the window to close
			log('tell the  Domoticzpopupblinds window to close', xbmc.LOGNOTICE)
			self.close()
		elif action == ACTION_MOVE_LEFT:
			self.setFocus(self.on)
		elif action == ACTION_MOVE_RIGHT:
			self.setFocus(self.off)
		elif action.getId() in ACTION_SELECT_ITEM:
			self.onClick(self.getFocusId())
			



class DomoticzWindow(xbmcgui.WindowXMLDialog):

	def __init__(self, *args, **kwargs):

		#~ #and define it as self
		log('running __init__ from DomoticzWindow class', xbmc.LOGDEBUG)

       
      
       
# INIT Function       
	def onInit(self):
		#tell the object to go read the log file, parse it, and put it into listitems for the XML
		log('running onInit from DomoticzWindow class', xbmc.LOGNOTICE)
		global __windowopen__
		__windowopen__=True
		self.populateFromDomo()
	
	
     # When we click on an item, if it's a switch, a scene or a group, we switch it, 
     # if it's a dimmer, let's make the popup appear
     # And then regenerate the window.
	def onClick(self, control):
		item = self.getControl(control).getSelectedItem()
		log("Click  "+item.getProperty('isswitch'),xbmc.LOGDEBUG)
		if item.getProperty('type') == 'switchscene' or item.getProperty('type') == 'switchlight':
			myargs={'idx':str(int(item.getProperty('idx'))),
					'type':'command',
					'param':item.getProperty('type'),
					'switchcmd':__opposite_status__[item.getProperty('data')]
					}
			sendcmd(myargs)
		elif item.getProperty('type') == 'blinds':
			args={'title':item.getLabel(), 'idx':item.getProperty('idx')}
			mydisplay = Domoticzpopupblinds(args)
			mydisplay.doModal()
			del mydisplay
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
			#tell the window to close
			global __windowopen__

			__windowopen__=False

			log('tell the window to close', xbmc.LOGNOTICE)
			self.close()


# The big thing.
	def populateFromDomo(self):
		results=transformDomoticz(getData())			# Ask domoticz for data
		self.getControl(120).reset()	# Reset the window. Used for update
		
		# A title
		item = xbmcgui.ListItem(label="XBMC Domoticz")			
		item.setProperty('istitle','true')
		self.getControl(120).addItem(item)
		
		odd=True	# Used to alernate the line colors.
		for myitem in results:
			
			log("Adding :"+myitem[u'Name'],xbmc.LOGDEBUG)

			# Adding the item, one line is grey, the next is black.  
			item = xbmcgui.ListItem(label=myitem[u'Name'],label2=myitem[u'Data'])
			item.setProperty('idx',myitem[u'Idx'])
			odd= not odd
			if odd:
				item.setProperty('isodd','true')
			else:
				item.setProperty('isodd','false')

			item.setProperty('type',myitem[u'Type'])
			# Data will be used when we click on the item.
			if u'Status' in myitem:
				item.setProperty('data',myitem[u'Status'])
			
			# Level will be used by the slider popup.
			if u'Level' in myitem:
				item.setProperty('level',str(myitem[u'Level']))

			# Set the icon
			item.setIconImage(myitem[u'Icon'])
			
			self.getControl(120).addItem(item)

 
 
class DomoticzWidgets(xbmcgui.Window):
	def __init__(self, *args, **kwargs):
		
		log("Init DomoticzWidgets")
		global __windowopen__

		__windowopen__=True

		# Widgets size
		self.widgetwidth=350
		self.widgetheight=60
		
		# Margins and screen size
		self.xoffset = 20
		self.yoffset = 50
		self.h=720
		self.w=1280
		
		# A few dicts
		self.backgrounds={}
		self.titles={}
		self.favs={}
		self.icons={}
		self.idx={}
		
		# Setting the background
		self.background=xbmcgui.ControlImage(0,0,self.w,self.h,filename=__images__+"speedfan-panel.png",aspectRatio=0)
		self.addControl(self.background)
		# And let's go !
		self.populateFromDomo()
		
		
	def CalcutateMargins(self,nbitems):
		log("NB Items : "+str(nbitems))

		# Calcutate values assuming screen will be full
		self.nbcol=int((self.w-2*self.xoffset)/self.widgetwidth)
		self.nbrow=int((self.h-2*self.yoffset)/self.widgetheight)

		if nbitems<self.nbcol*self.nbrow:
			# How many full rows ?
			fullrows=int( nbitems/self.nbcol)
			if cmp(fullrows,nbitems/self.nbcol):
				self.nbrow=min(self.nbrow,fullrows)
			else:
				self.nbrow=min(self.nbrow,fullrows+1)
	
		self.xspace=int((self.w-self.widgetwidth*self.nbcol-2*self.xoffset)/(self.nbcol+1))
		self.yspace=int((self.h-2*self.yoffset-self.widgetheight*self.nbrow)/(self.nbrow+1))


# This function generates the widgets, the optionnally only refreshes one.
	def populateFromDomo(self,idx=None):
		
		results=transformDomoticz(getData())			# Ask domoticz for data
		xbmc.executebuiltin( "ActivateWindow(busydialog)" )

		self.items={}
		i=1
		mycol=1
		myrow=1
		self.CalcutateMargins(len(results))
		
		for myitem in results:
			self.items[myitem[u'Type']+"-"+str(myitem[u'Idx'])]=myitem
			if i<=self.nbcol*self.nbrow+5:
				# Choose between only one to refresh or a full.
				if idx==None or idx==myitem[u'Type']+"-"+str(myitem[u'Idx']):
					self.addwidget(mycol,myrow,myitem[u'Name'],myitem[u'Type']+"-"+str(myitem[u'Idx']),myitem[u'Favorite'],myitem[u'Icon'],i,myitem[u'Data'])
				mycol=mycol+1
				if mycol==self.nbcol+1:
					mycol=1
					myrow=myrow+1
			i=i+1
		# Keys navigation
		i=1
		for myitem in results:
			self.backgrounds[i].setNavigation(self.backgrounds[self.navigation(i,"up")],self.backgrounds[self.navigation(i,"down")],self.backgrounds[self.navigation(i,"left")],self.backgrounds[self.navigation(i,"right")])
			i=i+1
		xbmc.executebuiltin( "Dialog.Close(busydialog)" )	
		self.focus(1)
		

# Maybe this function is no longer useful.
	def focus(self,focusid):
		self.setFocus(self.backgrounds[focusid])
	
	def RightClick(self,control):
		idx=self.idx[control]
		item=self.items[idx]
		args={'title':item[u'Name'], 'idx':item[u'Idx'],'fav':item[u'Favorite'],'type':item[u'Type']}
		mydisplay = DomoticzContext(args)
		mydisplay.doModal()
		del mydisplay
		if __favonly__=="true":
			self.populateFromDomo()
		else:
			self.populateFromDomo(idx)

	# When the user clicks on something
	def Click(self,control):
		
		idx=self.idx[control]
		item=self.items[idx]
		log("TYpe"+item[u'Name']+":"+item[u'Type'])
		if item[u'Type'] == 'switchscene' or item[u'Type'] == 'switchlight':
			myargs={'idx':str(item[u'Idx']),
				'type':'command',
				'param':item['Type'],
				'switchcmd':__opposite_status__[item['Status']]
			}
			sendcmd(myargs)
			self.populateFromDomo(self.idx[control])
		elif item[u'Type']  == 'blinds':
			args={'title':item[u'Name'], 'idx':item[u'Idx']}
			mydisplay = Domoticzpopupblinds(args)
			mydisplay.doModal()
			del mydisplay
			self.populateFromDomo(self.idx[control])
		elif item[u'Type'] == "dimmer":
			args={'title':item[u'Name'], 'idx':item[u'Idx'],'level':item[u'Level']}
			mydisplay = Domoticzpopupslider(args)
			mydisplay.doModal()
			del mydisplay
			self.populateFromDomo(self.idx[control])

# Define wich item we should go to
	def navigation(self,number,direction):
		if direction=="up":
			number=number-self.nbcol
		elif direction=="down":
			number=number+self.nbcol
		elif direction=="right":
			number=number+1
		elif direction=="left":
			number=number-1
		
		number=min(number,len(self.items))
		number=max(number,1)
		
		return number
		

# Creates or recreates a widget
	def addwidget(self,col,row,title,idx,fav,icon,focusid, data):
		log("Adding Widget" +" - " +title+" - "+str(idx))
		
		# Does the object already exist ?
		# If it does, let's just update it, if not, let's create it completely.
		if focusid in self.backgrounds:
			#~ log(title+"\n"+data)
			self.titles[focusid].setLabel(title+"\n"+data)
			self.icons[focusid].setImage(__images__+icon)
			if fav>0:
				self.favs[focusid].setImage(__images__+"favorite.png")
			else:
				self.favs[focusid].setImage(__images__+"nofavorite.png")
		else:
			x=(col-1)*(self.widgetwidth+self.xspace)+self.xspace+self.xoffset
			y=(row-1)*(self.widgetheight+self.yspace)+self.yspace+self.yoffset
			#~ log(str("W"+str(self.widgetwidth)))
			#~ log(str("H"+str(self.widgetheight)))
			self.backgrounds[focusid]=xbmcgui.ControlButton(x,y,self.widgetwidth,self.widgetheight,label='',noFocusTexture=__images__+"domoticz-panel.png")#,aspectRatio=0)
			self.idx[self.backgrounds[focusid].getId()]=idx
			#~ log(self.backgrounds[focusid].getId())
			self.titles[focusid]=xbmcgui.ControlLabel(x+60,y+5,self.widgetwidth-70,50,label=title+"\n"+data)
			if fav>0:
				self.favs[focusid]=xbmcgui.ControlImage(x+self.widgetwidth-35,y+15,16,16,filename=__images__+"favorite.png")
			else:
				self.favs[focusid]=xbmcgui.ControlImage(x+self.widgetwidth-35,y+15,16,16,filename=__images__+"nofavorite.png")
				
			self.icons[focusid]=xbmcgui.ControlImage(x+10,y+5,48,48,filename=__images__+icon)
			
			self.addControl(self.backgrounds[focusid])
			self.addControl(self.titles[focusid])
			self.addControl(self.favs[focusid])
			self.addControl(self.icons[focusid])
				
			self.idx[self.backgrounds[focusid].getId()]=idx
		#~ log(self.backgrounds[focusid].getId())
		
	def onAction(self, action):
		#~ captures user input and acts as needed
		#~ log('running onAction from DomoticzWidgets class', xbmc.LOGNOTICE)
		if(action == ACTION_PREVIOUS_MENU or action == ACTION_BACK):
			#if the user hits back or exit, close the window
			log('user initiated previous menu or back', xbmc.LOGNOTICE)
			#tell the window to close
			log('tell the window to close', xbmc.LOGNOTICE)
			global __windowopen__
			__windowopen__=False
			self.close()
		elif action.getId() in ACTION_SELECT_ITEM:
			self.Click(self.getFocusId())
		elif action.getId() in ACTION_CONTEXT_MENU:
			log("Right Click"+str(self.getFocusId()), xbmc.LOGNOTICE)
			self.RightClick(self.getFocusId())
		else:
			log("Something "+str(action.getId()), xbmc.LOGNOTICE)
			
	
#run the script
if ( xbmcgui.Window(10000).getProperty("domoticz.running") == "true" ):
    log('script already running, aborting subsequent run attempts', xbmc.LOGNOTICE)
else:
	#~ xbmcgui.Window(10000).setProperty( "domoticz.running",  "true" )
	if __view__ == VIEW_LIST:
		w = DomoticzWindow("domoticz.xml", __addonpath__, "Default")
		if __addon__.getSetting('refresh')=='true':
			t1 = Thread(target=updateWindow,args=("thread 1",w))
			t1.setDaemon(True)
			log('worker thread created. Attempting to start worker thread', xbmc.LOGNOTICE)
			t1.start()
		w.doModal()
		if __addon__.getSetting('refresh')=='true':	
			del t1
		del w
	elif __view__ == VIEW_WIDGET:
		w = DomoticzWidgets()
		if __addon__.getSetting('refresh')=='true':
			t1 = Thread(target=updateWindow,args=("thread 1",w))
			t1.setDaemon(True)
			log('worker thread created. Attempting to start worker thread', xbmc.LOGNOTICE)
			t1.start()
		w.doModal()
		if __addon__.getSetting('refresh')=='true':	
			del t1
		del w
	else:
		log("Wait ? What !?")
	xbmcgui.Window(10000).setProperty( "domoticz.running",  "false" )

