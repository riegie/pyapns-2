#!/usr/bin/env python

import apns
import sys
import time

if len(sys.argv) != 6:
    print "{} <cert-filename> <key-filename> <device-token> <numeric-id> "
    "<alert-text>".format(sys.argv[0])
else:
    push_conn = apns.Connection('gateway.sandbox.push.apple.com',
                                apns.PUSH_PORT, 'entrust.pem',
                                sys.argv[1], sys.argv[2])
    push_conn.write_push_msg(sys.argv[3], sys.argv[4], sys.argv[5])
    time.sleep(3)
    try:
        push_conn.check_for_error()
    except apns.error as e:
        print 'error: {}'.format(e)
