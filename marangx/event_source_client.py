# -+- encoding: utf-8 -+-
"""
.. module:: listener
:platform: Unix
:synopsis: This module provides an eventsource client based on tornado

.. moduleauthor:: Bernard Pratz <guyzmo@hackable-devices.org>
.. moduleauthor:: Ian Whyman
.. moduleauthor:: Коренберг Марк

"""
import time
import logging
log = logging.getLogger("eventsource.client")

from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

class Event(object):
    """
    Contains a received event to be processed
    """
    def __init__(self):
        self.name = None
        self.data = None
        self.id = None

    def __repr__(self):
        return "Event<%s,%s,%s>" % (str(self.id), str(self.name), str(self.data.replace("\n","\\n")))

class EventSourceClient(object):
    """
    This module opens a new connection to an eventsource server, and wait for events.
    """
    def __init__(self, url, callback = None, retry = 0, keep_alive = False, ssl = False, validate_cert = False, user = None, password = None):
        """
        Build the event source client
        :param url: string, the url to connect to
        :param action: string of the listening action to connect to
        :param target: string with the listening token
        :param callback: function with one parameter (Event) that gets called for each received event
        :param retry: timeout between two reconnections (0 means no reconnection)
        """
        log.debug("EventSourceClient(%s,%s,%s)" % (url, callback, retry))

        self.data_partial = None
        self.last_event_id = None
        self.retry_timeout = int(retry)
        self.keep_alive = keep_alive
        self._url = url
        self._headers = {"Accept": "text/event-stream"}
        self._user = user
        self._password = password

        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        self.http_client = AsyncHTTPClient()
        self.http_request = HTTPRequest(url = self._url,
                                        method="GET",
                                        headers={"content-type":"text/event-stream"},
                                        request_timeout = 0,
                                        validate_cert = validate_cert,
                                        streaming_callback = self.handle_stream,
                                        auth_username = user,
                                        auth_password = password)
        if callback is None:
            self.cb = lambda e: log.info( "received %s" % (e,) )
        else:
            self.cb = callback

    def _get_headers(self):
        """
        Provide headers to be used for next request. By default checks for
        self.last_event_id and populates a header as needed.
        """
        if self.last_event_id:
            self._headers["Last-Event-ID"] = self.last_event_id
        return self._headers

    def _get_request(self):
        """
        Return a suitablty initialized HTTPRequest
        """
        return HTTPRequest(url = self._url,
                           method="GET",
                           headers = self._get_headers(),
                           request_timeout = 0,
                           streaming_callback = self.handle_stream,
                           auth_username = self._user,
                           auth_password = self._password)

    def poll(self):
        """
        Function to call to start listening
        """
        log.debug("poll()")

        while True:
            self.http_client.fetch(self._get_request(), self.handle_request)
            IOLoop.instance().start()
            if self.retry_timeout == -1:
                break
            time.sleep(self.retry_timeout/1000)

    def end(self):
        """
        Function to call to end listening
        """
        log.debug("end()")

        self.retry_timeout=-1
        IOLoop.instance().stop()

    def handle_stream(self, message):
        """
        Acts on message reception
        :param message: string of an incoming message

        parse all the fields and builds an Event object that is passed to the callback function
        """
        log.debug("handle_stream(...)")
        message = message.decode()
        if not message.endswith("\n"):
            log.debug("got partial chunk")
            if self.data_partial:
                self.data_partial += message
            else:
                self.data_partial = message
            return

        if self.data_partial:
            log.debug("rebuiling chunked response")
            message = self.data_partial + message
            self.data_partial = None

        event = Event()
        event_list = message.strip().splitlines()
        if len(event_list) < 1:
            return
        for line in event_list:
            if line:
                (field, value) = line.split(": ")
                field = field.strip()

                if field == "event":
                    event.name = value.lstrip()
                elif field == "data":
                    value = value.lstrip()
                    if event.data is None:
                        event.data = value
                    else:
                        event.data = "%s\n%s" % (event.data, value)
                elif field == "id":
                    event.id = value.lstrip()
                    self.last_event_id = event.id
                elif field == "retry":
                    try:
                        self.retry_timeout = int(value)
                        log.info( "timeout reset: %s" % (value,) )
                    except ValueError:
                        pass
                elif field == "":
                    log.debug( "received comment: %s" % (value,) )
                else:
                    pass
        if event.name is not None:
            self.cb(event)

    def handle_request(self, response):
        """
        Function that gets called on non long-polling actions,
        on error or on end of polling.

        :param response: tornado's response object that handles connection response data
        """
        log.debug("handle_request(response=%s)" % (response,))

        if response.code in (200, 500, 502, 503, 504):
            log.debug("Connection completed, reconnecting")
        elif response.error:
            log.error(response.error)
            if not self.keep_alive:
                self.retry_timeout=-1
        else:
            log.info("disconnection requested")
            if not self.keep_alive:
                self.retry_timeout=-1
        IOLoop.instance().stop()