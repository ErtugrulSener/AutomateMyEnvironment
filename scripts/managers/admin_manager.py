#!/usr/bin/env python
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010
# Released under the same license as Python 2.6.5


import ctypes
import os
import sys
import traceback
import types

import win32con
import win32event
import win32process
from win32com.shell import shellcon
from win32com.shell.shell import ShellExecuteEx

from scripts.logging.logger import Logger
from scripts.singleton import Singleton

logger = Logger.instance()


@Singleton
class AdminManager:
    def is_user_admin(self):
        if os.name == 'nt':
            # WARNING: requires Windows XP SP2 or higher!
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                traceback.print_exc()
                logger.error("Admin check failed, assuming not an admin.")
                return False
        elif os.name == 'posix':
            # Check for root on Posix
            return os.getuid() == 0
        else:
            raise RuntimeError("Unsupported operating system for this module: %s" % (os.name,))

    def run_as_admin(self, cmd_line=None, wait=True):
        if os.name != 'nt':
            raise RuntimeError("This function is only implemented on Windows.")

        python_exe = sys.executable

        if cmd_line is None:
            cmd_line = [python_exe] + sys.argv
        elif type(cmd_line) not in (types.TupleType, types.ListType):
            raise ValueError("cmdLine is not a sequence.")

        cmd = '"%s"' % (cmd_line[0],)
        # XXX TODO: isn't there a function or something we can call to massage command line params?
        parameters = " ".join(['"%s"' % (x,) for x in cmd_line[1:]])

        show_command = win32con.SW_SHOWNORMAL
        # showCmd = win32con.SW_HIDE
        lpVerb = 'runas'  # causes UAC elevation prompt.

        # print "Running", cmd, params

        # ShellExecute() doesn't seem to allow us to fetch the PID or handle
        # of the process, so we can't get anything useful from it. Therefore
        # the more complex ShellExecuteEx() must be used.

        process_info = ShellExecuteEx(nShow=show_command,
                                      fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                      lpVerb=lpVerb,
                                      lpFile=cmd,
                                      lpParameters=parameters)

        if wait:
            process_handle = process_info['hProcess']
            obj = win32event.WaitForSingleObject(process_handle, win32event.INFINITE)
            rc = win32process.GetExitCodeProcess(process_handle)
        else:
            rc = None

        return rc
