import json
import re
import select
import socket
import ssl
import struct

PUSH_PORT = 2195
FEEDBACK_PORT = 2196
ERROR_MSGS = {0: "no error",
              1: "processing error",
              2: "missing device token",
              3: "missing topic",
              4: "missing payload",
              5: "invalid token size",
              6: "invalid topic size",
              7: "invalid payload size",
              8: "invalid token",
              255: "none (unknown)"}

def build_msg(device_token, msg_id, alert):

    """ Build a message for sending to APNs.

    It is in the "extended" binary format. This is a bare function, not an
    instance method because some programs--such as tests or offline batch
    creators--might need to build messages, but not need the connection
    established by instances of the "connection" class.

    """

    msg_id = int(msg_id)

    if re.search('^[0-9a-fA-F]+$', device_token) == None:
        raise ValueError("failed: device token ({}) not a valid " +
                         "hex string.".format(device_token))
    token_len = len(device_token)
    if (token_len % 2) != 0:
        raise ValueError("failed: device token ({}) has an odd " +
                         "number of characters ({})".format(device_token,
                                                            token_len))

    payload = json.dumps({'aps': {'alert': alert}})
    payload_len = len(payload)
    token_bytes = device_token.decode("hex")
    token_len = len(token_bytes)

    return struct.pack("!bIIH{}sH{}s".format(token_len, payload_len),
                       1, msg_id, 0, token_len, token_bytes,
                       payload_len, payload)

class Error(Exception):
    """ Encapsulates an error returned by the APNs.

    connection.check_for_error  will raise this exception if if reads an
    error from the connection.

    """

    def __init__(self, error):
        
        if error == None:
            self.msg_id = 0
            self.error_code = None
        else:
            error_fields = struct.unpack('!BBI', error)
            self.msg_id = error_fields[2]
            self.error_code =  error_fields[1]

    def __str__(self):

        try:
            msg = ERROR_MSGS[self.error_code]
        except KeyError:
            msg = 'unknown code: {}'.format(self.error_code)
            
        return msg



class Connection:

    """Implement a connection to APNs."""

    def __init__(self, host, port, ca_file, cert_file, pkey_file):

        """ Connect to APNs.

        This sets up the TLS session to an Apple push server, sending the
        provider certificate and verifying the certificate Apple sends.

        """

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = ssl.wrap_socket(s, ca_certs=ca_file,
                                      cert_reqs=ssl.CERT_REQUIRED,
                                      keyfile=pkey_file, certfile=cert_file)
                                      
        self.socket.connect((host, port))


    def write_push_msg(self, device_token, msg_id, alert):
        """ Build a message and send it to APNs. """

        self.socket.write(build_msg(device_token, msg_id, alert))

    def read_feedback_msg(self, log_file):

        """ Read an entry from the feedback service.

        Notes:

        - It's OK to just keep reading until nil is returned. The feedback
        service will close the connection when there are no more entries
        and a final read is performed.
        
        - Reading the responses removes the discovered tokens from the
        feedback service. Hence, the data must either be saved or acted
        on immediately. Don't just run this method from a command line
        utility that discards the output.
        
        - The read method blocks until it gets the requested amount of data,
        or an unexpected EOF occurs, in which case it returns less than
        requested. This is treated as an error.

        """

        # The first part of the message is fixed-length and contains the
        # "dead_at" timestamp and the length of the token.
        part1 = self.socket.read(6)
        part1_len = len(part1)
        if part1_len == 6:
            fields = struct.unpack('!iH', part1)
            dead_at = fields[0]
            token_len = fields[1]

            # The remainder is the device token. Practically speaking, it's
            # always 32 bytes, but a length is sent in the "initial" part
            # of the message, so that value is used in the next read's length.
            part2 = self.socket.read(token_len)
            part2_len = len(part2)
            if len(part2) == token_len:
                fields = struct.unpack('{}s'.format(token_len), part2)
                token = fields[0]
                token_hex = "".join("{0:x}".format(ord(c)) for c in token)
                device_info = {'token': token_hex, 'dead_at': dead_at}
            else:
                print 'incomplete device id '
                '(expected {}, got {}'.format(token_len, part2_len)
                device_info = None

        else:
            if part1_len != 0:
                print 'unexpected header length ({} bytes)'.format(part1_len)
            device_info = None

        return device_info

    def check_for_error(self):

        """ Poll for (and read) errors from the APNs.

        This should be called during push sessions to verify that no errors
        have occurred. If errors have occured, this raises an exception that
        contains the device token and message id. Calling programs can use
        this, along with the complete list of devices, to resume sending.

        """

        ready = select.select([self.socket], [], [], 0)
        if (len(ready[0])):
            raise error(self.socket.read(6))

    def close_connection(self):
    
        """ Close the connection to APNs.

        Most programs will not need this because they simply create a
         session and then terminate.

         """

        if self.socket != None:
            self.socket.close()
            self.socket = None

        
