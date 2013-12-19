import xbmc, xbmcgui
import urllib2
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

user="admin"
password="12frroeodt"
url="http://www.bbrose.net/domoticz/json.htm?type=devices&filter=all&used=true&order=Name"

passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
# this creates a password manager
passman.add_password(None, url, user, password)
# because we have put None at the start it will always
# use this username/password combination for  urls
# for which `theurl` is a super-url

authhandler = urllib2.HTTPBasicAuthHandler(passman)
# create the AuthHandler

opener = urllib2.build_opener(authhandler)

urllib2.install_opener(opener)
# All calls to urllib2.urlopen will now use our handler
# Make sure not to include the protocol in with the URL, or
# HTTPPasswordMgrWithDefaultRealm will be very confused.
# You must (of course) use it when fetching the page though.




#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_PREVIOUS_MENU = 10
 
class MyClass(xbmcgui.Window):
  def __init__(self):
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    self.strActionInfo = xbmcgui.ControlLabel(250, 80, 200, 200, '', 'font14', '0xFFBBBBFF')
    self.addControl(self.strActionInfo)
    self.strActionInfo.setLabel('Push BACK to quit')
    self.list = xbmcgui.ControlList(200, 150, 400, 400, selectedColor = '0xFF0000')
    self.addControl(self.list)
    results=self.getData()
    for item in results[u'result']:
      self.list.addItem(item[u'Name']+" "+item[u'Data'])

    self.setFocus(self.list)
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )


  def onAction(self, action):
    #self.message('You did : ' + action)
    if action == ACTION_PREVIOUS_MENU:
      self.close()
 
  def onControl(self, control):
    if control == self.list:
      item = self.list.getSelectedItem()
      self.message('You selected : ' + item.getLabel())  
 
  def message(self, message):
    dialog = xbmcgui.Dialog()
    dialog.ok(" My message title", message)
    
  def getData(self):
    pagehandle = urllib2.urlopen(url)
    # authentication is now handled automatically for us
    html = pagehandle.read()
    pagehandle.close()
    return simplejson.loads(html)


mydisplay = MyClass()
mydisplay.doModal()
del mydisplay
