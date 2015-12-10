#!/usr/bin/python

import urllib2, base64, sys, logging, getpass, json, re, os
from pprint import pprint
from xml.dom import minidom

reload(sys)
sys.setdefaultencoding('utf8')

# Store Vars permanently in the script here, else get prompted later.
jssuser = ''
jsspass = ''
jssserver = ''
resultsFile = 'appUpdateResults.txt'

# Setup logging
resultsFile = os.path.dirname(os.path.realpath(__file__)) + "/" + resultsFile
logging.basicConfig(filename=resultsFile, level=logging.DEBUG, filemode='w')

# Output formaters
indent = '     '
# Terminal Colors
class printColor:
    green = '\033[92m'
    red = '\033[91m'
    yellow = '\033[93m'
    end = '\033[0m'

# Emojis
star = '\xE2\xAD\x90'
oksign = '\xF0\x9F\x91\x8C'
errorsign = '\xE2\x9D\x97'

# iTunes Lookup URL
itunes = 'https://itunes.apple.com/lookup?id='

# Find out the connection info
if not jssuser:
    jssuser = raw_input('Enter JSS User Account: ')
if not jsspass:
    jsspass = getpass.getpass('Enter JSS Password: ')
if not jssserver:
    jssserver = raw_input('Enter the JSS Server URL: ')


def jssgetapps():
    getApplications = urllib2.Request(jssserver + '/JSSResource/mobiledeviceapplications')
    getApplications.add_header('Authorization', 'Basic ' + base64.b64encode(jssuser + ':' + jsspass))
    try:
        applications = minidom.parse(urllib2.urlopen(getApplications))
        return applications.getElementsByTagName('mobile_device_application')
    except urllib2.HTTPError, checkResponseError:
        print '{0}There was a server error while retrieving the applications list from the JSS.{1}'.format(
            printColor.red, printColor.end)
        logging.debug(
            'ERROR: Error connecting to JSS: There was a server error while retrieving the applications list from the '
            'JSS.')

def jssgetappitunesurl(id):
    getapp = urllib2.Request(jssserver + '/JSSResource/mobiledeviceapplications/id/' + id)
    getapp.add_header('Authorization', 'Basic ' + base64.b64encode(jssuser + ':' + jsspass))

    try:
        app = minidom.parse(urllib2.urlopen(getapp))
    except urllib2.HTTPError, checkResponseError:
        print '{0}There was a server error while retrieving the application from the JSS.{1}'.format(printColor.red,
                                                                                                     printColor.end)
        logging.debug('ERROR: Error connecting to JSS while retreiving information about application ' + id + ".")
    try:
        url = unicode(app.getElementsByTagName('itunes_store_url')[0].firstChild.data)
        urlid = re.search('/id(.+?)\?mt=', url).group(1)
    except AttributeError:
        return
    return urlid


def fetchitunesversion(itunesid):
    # logging.debug("Checking iTunes URL:" + itunes + itunesid)
    try:
        itunesresponse = json.loads(urllib2.urlopen(itunes + itunesid).read())
    except urllib2.HTTPError:
        print '{0}Unable to check application version with iTunes.{1}'.format(printColor.red, printColor.end)
        logging.debug('ERROR: Unable to check application version with iTunes.')

    if itunesresponse["resultCount"] > 0:
        return itunesresponse["results"][0]["version"]
    else:
        return 0


apps = jssgetapps()
appcounts = len(apps)

print('{0}Found {1} apps.{2}'.format(printColor.green,str(appcounts),printColor.end))
logging.debug('{0}INFO: Found {1} apps.{2}'.format(printColor.green,str(appcounts),printColor.end))

for a in apps:
    # Define some variables about this app
    appname = a.getElementsByTagName('display_name')[0].childNodes[0].data
    appid = a.getElementsByTagName('id')[0].childNodes[0].data
    appversion = a.getElementsByTagName('version')[0].childNodes[0].data

    # Check iTunes for the latest version
    appitunesurlid = jssgetappitunesurl(appid)
    appitunesversion = fetchitunesversion(appitunesurlid)

    # Write to results
    logging.info(star + indent + 'Checking: ' + appname)
    logging.info(indent + indent + 'Version in JSS: ' + appversion)
    if appitunesversion > 0:
        logging.info('{0}{1}Current Version in iTunes: {2}'.format(indent, indent, appitunesversion))
    else:
        logging.debug('{0}{1}{2}ERROR: Application not found in iTunes.{3}'.format(printColor.red, indent, indent, printColor.end))

    # Output to user
    print '{0}{1}Checking: {2}'.format(star, indent, appname)
    print '{0}{1}Version in JSS: {2}'.format(indent, indent, appversion)
    if appitunesversion > 0:
        print '{0}{1}Current Version in iTunes: {2}'.format(indent, indent, appitunesversion)
        if appversion < appitunesversion:
            print '{0}{1}{2}Update available!'.format(errorsign,indent,indent)
            logging.info('{0}{1}{2}Update available!'.format(errorsign,indent,indent))
        else:
            print '{0}{1}{2}Application up to date.'.format(oksign,indent,indent)
            logging.info('{0}{1}{2}Application up to date.'.format(oksign,indent,indent))
    else:
        print "{0}{1}{2}Application not found in iTunes.{3}".format(printColor.red, indent, indent, printColor.end)
