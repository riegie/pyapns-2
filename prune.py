#!/usr/bin/env python

import apns
import sys

if len(sys.argv) != 3:
  print 'usage: {} <cert-filename> <key-filename>'.format(sys.argv[0])
else:
    feedback_conn = apns.Connection('gateway.sandbox.push.apple.com',
                                    apns.FEEDBACK_PORT, 'entrust.pem',
                                    sys.argv[1], sys.argv[2])

    count = 0
    more = True
    while more:
      device_info = feedback_conn.read_feedback_msg(sys.stderr)
      more = (device_info != None)
      if more:
        count += 1
        print '{} dead_at: {}'.format(device_info['token'],
                                      device_info['dead_at'])

    print '{} dead devices.'.format(count)
