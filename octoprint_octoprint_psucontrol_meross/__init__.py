# coding=utf-8
from __future__ import absolute_import

__author__ = "Olivier Jan <ojanhk@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2021 Olivier Jan - Released under terms of the AGPLv3 License"

import asyncio
import os
import nest_asyncio

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.model.http.exception import TooManyTokensException, TokenExpiredException, AuthenticatedPostException, \
    HttpApiError, BadLoginException

import octoprint.plugin
import socket
import json
from struct import unpack
from builtins import bytes
import struct

nest_asyncio.apply()

class PSUControl_Meross(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.RestartNeedingPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin,
                        octoprint.plugin.ShutdownPlugin):

    def __init__(self):
        self.config = dict()


    def get_settings_defaults(self):
        return dict(
            username = '',
            password = '',
            plug = 0
        )


    def on_settings_initialized(self):
        self.reload_settings()


    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))

    async def meross_shutdown(self): 
        self.manager.close()
        await http_api_client.async_logout()

    async def meross_init(self):
        try:
            http_api_client = await MerossHttpClient.async_from_user_password(email=self.config['username'], password=self.config['password'])
        except BadLoginException:
            self._logger.info("Invalid username/Password combination")
            return

        # Setup and start the device manager
        self.manager = MerossManager(http_client=http_api_client)
        await self.manager.async_init()

        # Retrieve all the MSS310 devices that are registered on this account
        self.plugs =  await self.manager.async_device_discovery()

        if len(self.plugs) < 1:
            self._logger.info("No MSS425F plugs found...")
        else:
            self._logger.info("Found {} devices".format(len(self.plugs)))
            for i in range(len(self.plugs)):
                await self.plugs[i].async_update()
                self._logger.info("Device {} name is {}".format(i,self.plugs[i].name))
                if(len(self.plugs[i].channels)>1):
                    self._logger.info("{} has {} channels".format(self.plugs[i].name, len(self.plugs[i].channels)))
                    for j in range(len(self.plugs[i].channels)):
                        self._logger.info("........{} is {}".format(self.plugs[i].channels[j].name,self.plugs[i].is_on(j)))


    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return
        psucontrol_helpers['register_plugin'](self)
        asyncio.run(self.meross_init())

    def on_shutdown():
        asyncio.run(self.meross_shutdowm())
        

    async def change_psu_state(self, state):
        if state == 1:
            await self.plugs[0].async_turn_on(channel=self.config['plug'])
        else:
            await self.plugs[0].async_turn_off(channel=self.config['plug'])
        self._logger.info("Changing PSU state")

    def turn_psu_on(self):
        self._logger.debug("Switching PSU On")
        try:
            asyncio.run(self.change_psu_state(1))
        except RuntimeError:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(self.change_psu_state(1))
        
    def turn_psu_off(self):
        self._logger.debug("Switching PSU Off")
        try:
            asyncio.run(self.change_psu_state(0))
        except RuntimeError:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(self.change_psu_state(0))


    def get_psu_state(self):
        self._logger.debug("get_psu_state")
        result = self.plugs[0].is_on(self.config['plug'])    
        return result

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()


    def get_settings_version(self):
        return 1


    def on_settings_migrate(self, target, current=None):
        pass


    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]


    def get_update_information(self):
        return dict(
            psucontrol_meross=dict(
                displayName="PSU Control - Meross",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="olivierjan",
                repo="OctoPrint-PSUControl-Meross",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/olivierjan/OctoPrint-PSUControl-Meross/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "PSU Control - Meross"
__plugin_pythoncompat__ = ">=3.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_Meross()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
