# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright © 2009-2014, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
 *
 *  Mumble-Django is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

# This is somewhat ugly, but it makes life much easier.
import os
os.environ['MURMUR_CONNSTR']   = 'Meta:tcp -h 127.0.0.1 -p 6502'
os.environ['MURMUR_ICESECRET'] = ''

import mock

from django.test import TestCase

from mumble.models import MumbleServer, Mumble, MumbleUser

class IceTestCase(TestCase):
    def test_loadSlice_getSliceDir(self):
        with mock.patch("mumble.MumbleCtlIce.Ice") as mock_Ice:
            mock_Ice.getSliceDir.return_value = "/tmp/slice"

            from mumble.MumbleCtlIce import loadSlice
            loadSlice("someslice")

            self.assertTrue( mock_Ice.loadSlice.called)
            self.assertEqual(mock_Ice.loadSlice.call_count, 1)
            self.assertEqual(mock_Ice.loadSlice.call_args[0], ('', ['-I/tmp/slice', 'someslice']))

    def test_loadSlice_getSliceDir_empty(self):
        with mock.patch("mumble.MumbleCtlIce.Ice") as mock_Ice:
            mock_Ice.getSliceDir.return_value = ""

            from django.conf import settings
            from mumble.MumbleCtlIce import loadSlice
            loadSlice("someslice")

            self.assertTrue( mock_Ice.loadSlice.called)
            self.assertEqual(mock_Ice.loadSlice.call_count, 1)
            self.assertEqual(mock_Ice.loadSlice.call_args[0], ('', ['-I' + settings.SLICEDIR, 'someslice']))

    def test_loadSlice_getSliceDir_nonexistant(self):
        with mock.patch("mumble.MumbleCtlIce.Ice") as mock_Ice:
            mock_Ice.mock_add_spec(["loadSlice"])

            from django.conf import settings
            from mumble.MumbleCtlIce import loadSlice
            loadSlice("someslice")

            self.assertTrue( mock_Ice.loadSlice.called)
            self.assertEqual(mock_Ice.loadSlice.call_count, 1)
            self.assertEqual(mock_Ice.loadSlice.call_args[0], ('', ['-I' + settings.SLICEDIR, 'someslice']))

    def test_MumbleCtlIce(self):
        with mock.patch("mumble.MumbleCtlIce.Ice")    as mock_Ice,   \
             mock.patch("mumble.MumbleCtlIce.IcePy")  as mock_IcePy, \
             mock.patch("Murmur.MetaPrx")             as mock_MetaPrx:

            mock_MetaPrx.checkedCast().getVersion.return_value = (1, 2, 3, "12oi3j1")

            from mumble.MumbleCtlIce import MumbleCtlIce
            ctl = MumbleCtlIce('Meta:tcp -h 127.0.0.1 -p 6502')

            self.assertTrue( mock_Ice.createProperties().setProperty.called)
            self.assertEqual(mock_Ice.createProperties().setProperty.call_count, 2)
            self.assertEqual(mock_Ice.createProperties().setProperty.call_args_list[0][0], ("Ice.ImplicitContext", "Shared"))
            self.assertEqual(mock_Ice.createProperties().setProperty.call_args_list[1][0], ("Ice.MessageSizeMax",  "65535"))

            mock_prx = mock_Ice.initialize().stringToProxy()
            self.assertTrue( mock_prx.ice_ping.called)

