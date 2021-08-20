# OctoPrint-PSUControl-Meross

This plug-in for PSU Control enables usage of Meross plugs. 
It's very basic and has been tested only with MSS425F so far, but it should be easily modified for other Meross plugs.  

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/olivierjan/OctoPrint-PSUControl-Meross/archive/master.zip


## Configuration

After installation, go to the plug-in settings and enter your user, password and the number of the plug you want to manage.
Once done, restart OctoPrint and go to PSU Control configuration. I would suggest changing the Sensing option in PSU Control settings to something higher than 5 seconds (I use 900 seconds). 

## Thanks 

Many thanks to [Thimotée Girard](https://github.com/timgir) for his excellent Meross plug-in.