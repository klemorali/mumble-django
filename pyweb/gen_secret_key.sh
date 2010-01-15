#!/bin/bash
#
#  Update settings.py with an automatically generated Secret Key.
#
#  Copyright © 2009-2010, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>
#
#  Mumble-Django is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This package is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

HASHSCRIPT='
from hashlib import sha1;
import sys;
print sha1( sys.stdin.read() ).hexdigest();'

KEY=` dd if=/dev/urandom bs=64 count=1 2>/dev/null | python -c "$HASHSCRIPT" `
SECKEY="SECRET_KEY = '$KEY'"

sed -ie "s/^SECRET_KEY.*/${SECKEY}/" settings.py
