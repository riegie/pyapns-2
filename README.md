# PyAPNs

A Python library for Apple Push Notifications

## Introduction

PyAPNs allows communication with the Apple Push Notifiction Service (APNs). The API is a binary protocol in which clients connect via SSL and then one side blasts packets at the other until it's done (or an error occurs). There are two operations: sending push notifications and receiving a list of dead clients. In the first operation, it's the client that does the talking; in the second, it's the APNs service.

## Design

PyAPNs is a module with two classes and a couple of non-instance-specific odds and ends. One class implements the actual protocol. Another is an exception class that inherits from Exception. If something goes wrong, the implementation raises an instance of the exception.

In addition to the class, three sample programs are included that make use of its features. `push.py` sends a message to a specific device, specified by a 64 character hex string. `prune.py` retrieves and prints a list of devices believed dead by APNs. `build.py` is similar to `push.py`, but simply prints the formatted message to the standard out, rather than sending it to the APNs server.

## API

The constructor of the `connection` class opens an SSL connection to an APNs server (notification or feedback, depending on the specified port number). It has the following methods.

- `write_push_msg` uses the class method above and sends it to the server specified when the object was created.

- `read_feedback_msg` read information about a dead device from the Feedback service. It returns a hash with `:token` and `:dead_at` keys.

- `check_for_error` raises a PushError exception if it is able to read an error message from the connection used to send notifications. It is intended to be called in the loop that sends a series of notifications to the APNs service.

The `error` class is based on the standard Python exception class. You (the application developer) don't create these. The `connection` class raises them if something goes wrong.

The non-instance specfic stuff is the following:

- Convenience constants that provide easy-to-remember stand-ins for the two port numbers used by the APNs.

- A table that maps APNs error codes to text strings. This is used by the `error` exception class.

- The `build_msg` function takes notification data and encodes it into the APNs "extended" format, which is a packed binary encoding. Programs can use this to build messages without sending them, or even needing to create an instance (which connects to a server). Normal programs will use `write_push_msg` instead of this.

## Integration Into Real-World Systems
Any interaction with APNs necessarily involves using and maintaining large lists of device tokens. In practice, these will be stored in a database. It's the responsibility of library clients to provide the necessary glue between the library and the datastore. This kind of glue is not hard to build, but it usually is application specific.

Another aspect of APNs is the rigamarole surrounding the creating of keys, certificates and the association of these items with the application to which you'd like to send notifications. I can provide some guidance on this. It's tedious but not all that difficult to understand.
