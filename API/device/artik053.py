# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base

import connection
import re
import signal
import time

from ..common import (console, paths, utils)


class Device(base.DeviceBase):
    '''
    Artik053 device class. (Only for testing the testrunner.)
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('artik053', remote_path='/')
        self.serial = connection.serialcom.Connection(options, 'TASH>>')
        self.platform = utils.get_system().lower() + utils.get_architecture()

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        pass

    def get_test_path(self):
        '''
        Return the test path on the device.
        '''
        return '/rom/test'

    def flash(self, os):
        '''
        Flash the given operating system to the board.
        '''
        utils.execute(paths.TIZENRT_OS_PATH, 'make', ['download', 'ALL'])

    def reset(self):
        '''
        Reset the board.
        '''
        utils.execute(paths.TIZENRT_OPENOCD_PATH, './%s/openocd' % self.platform,
            ['-f', 'artik053.cfg', '-c', 'reset'], quiet=True)

        # Wait a moment to boot the device.
        time.sleep(2)

    def login(self):
        '''
        Create connection.
        '''
        try:
            self.serial.open()

            # Press enters to start the serial communication and
            # go to the test folder because some tests require resources.
            self.serial.exec_command('\n\n')
            self.serial.exec_command('cd /rom/test')

        except Exception as e:
            console.fail(str(e))

    def logout(self):
        '''
        Close connection.
        '''
        self.serial.close()

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        self.reset()
        self.login()

        # Send testrunner command to the device and process its result.
        self.serial.putc('%s %s\n' % (cmd, ' '.join(args).encode('utf8')))
        self.serial.readline()
        message, stdout = self.serial.read_until(self.serial.get_prompt(),
            'AssertionError', 'uncaughtException', 'arm_dataabort')

        exitcode = 1
        if message == self.serial.get_prompt():
            # Find the test result from stdout.
            match = re.search('RESULT: (\d+)', stdout)
            if match:
                exitcode = match.group(1)
            else:
                exitcode = 1
        else:
            stdout += self.serial.readline().replace('\n', '')
            print(stdout)

        #TODO: Add memory result.
        return exitcode, stdout, 'n/a'
