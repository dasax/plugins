#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2017      Daniel Frank                knx-user-forum.de:dafra 
#########################################################################
# This file is part of SmartHome.py. http://mknx.github.io/smarthome/
#
# SmartHome.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SmartHome.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
from lib.model.smartplugin import SmartPlugin
from datetime import datetime, timedelta
import os
import time
import threading

logger = logging.getLogger(__name__)

class RCswitch(SmartPlugin):

	ALLOW_MULTIINSTANCE = False
	PLUGIN_VERSION = "0.1"

	def __init__(self, smarthome, rcswitch_dir='/usr/local/bin/rcswitch-pi', rcswitch_sendDuration='0.5'):
		logger.info('Init RCswitch')
		self.setupOK = True
		self._sh=smarthome
		
		# Check optional Parameters: check Path
		# Step 1: format string: cut possible '/' at end of rcswitch_dir parameter
		if rcswitch_dir[len(rcswitch_dir)-1] == '/':
			self.rcswitch_dir = rcswitch_dir[0:len(rcswitch_dir)-1]
		else:
			self.rcswitch_dir = rcswitch_dir

		# Step 2: check if rc switch is installed at the specified path
		if not os.path.isfile('{}/send'.format(self.rcswitch_dir)):
			logger.error('RCswitch: send file of RCswitch not found at {}. Check if RCswitch is installed correctly and path is set correctly in logic.conf.'.format(self.rcswitch_dir))
			self.setupOK = False
			
		# Check optional Parameters: check sendDuration
		try:
			self.sendDuration = float(rcswitch_sendDuration)
		except Exception as e:
			self.sendDuration = float(0.5)
			logger.warning('RCswitch: Argument {} for rcswitch_sendDuration is not a valid number. Using default value instead.'.format(rcswitch_sendDuration))
			
		# setup semaphore
		self.lock = threading.Lock()
		
	def run(self):
		self.alive = True

	def stop(self):
		self.alive = False

	def parse_item(self, item):
		# generate warnings for incomplete configured itemns
		if 'rc_device' in item.conf:
			if 'rc_code' in item.conf:
				return self.update_item
			else:
				logger.warning('RC Switch: attribute rc_code for {} missing. Item will be ignored by RCswitch plugin'.format(item))
				return None
		elif 'rc_code' in item.conf:
			logger.warning('RC Switch: attribute rc_device for {} missing. Item will be ignored by RCswitch plugin'.format(item))
			return None
		else:
			return None


	def update_item(self, item, caller=None, source=None, dest=None):
		# send commands to devices
		if 'rc_device' in item.conf and 'rc_code' in item.conf and self.setupOK:
			# prepare parameters
			value = item()
			rcCode = item.conf['rc_code']
			rcDevice = item.conf['rc_device']
			
			# avoid parallel access by use of semaphore
			self.lock.acquire()
			os.popen('{}/send {} {} {}'.format(self.rcswitch_dir, rcCode, rcDevice, int(value)))
			logger.info('RC Switch: setting device {} with system code {} to {}'.format(rcDevice, rcCode, value))
			time.sleep(min(self.sendDuration,10))# give the transmitter time to complete sending of the command (but not more than 10s)
			self.lock.release()