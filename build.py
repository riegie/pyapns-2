#! /usr/bin/env python

import apns
import sys

if len(sys.argv) == 4:
    print apns.build_msg(sys.argv[1], sys.argv[2], sys.argv[3])
else:
    print "{} <device-token> <numeric-id> <alert-text>".format(sys.argv[0])
