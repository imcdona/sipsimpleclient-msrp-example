#!/usr/bin/python3

from application.notification import NotificationCenter
from sipsimple.account import AccountManager
from sipsimple.application import SIPApplication
from sipsimple.core import SIPURI, ToHeader
from sipsimple.lookup import DNSLookup, DNSLookupError
from sipsimple.storage import FileStorage
from sipsimple.session import Session
from sipsimple.streams.msrp.chat import ChatStream
from sipsimple.threading.green import run_in_green_thread
from threading import Event

CALLER_ACCOUNT = 'andriy.makukha@sip2sip.info'  # must be configured in config/config
TARGET_URI = 'sip:echo@conference.sip2sip.info'  # SIP URI we want to call

class SimpleMSRPApplication(SIPApplication):

    def __init__(self):
        SIPApplication.__init__(self)
        self.ended = Event()
        self.callee = None
        self.session = None
        self.chat_stream = None
        notification_center = NotificationCenter()
        notification_center.add_observer(self)

    def call(self, callee):
        print('Placing MSRP call to', callee)
        self.callee = callee
        self.start(FileStorage('config'))  # Start the SIP application

    @run_in_green_thread
    def _NH_SIPApplicationDidStart(self, notification):
        print('Callback: application started')
        self.callee = ToHeader(SIPURI.parse(self.callee))
        # Retrieve account from config
        try:
            account = AccountManager().get_account(CALLER_ACCOUNT)
            host = account.sip.outbound_proxy.host
            port = account.sip.outbound_proxy.port
            transport = account.sip.outbound_proxy.transport
            print('Host = %s\nPort = %s\nTransport = %s' % (host, port, transport))
        except Exception as e:
            print('ERROR:', e)
        try:
            uri = SIPURI(host=host, port=port, parameters={'transport': transport})
            routes = DNSLookup().lookup_sip_proxy(uri, ['tcp', 'udp']).wait()
        except DNSLookupError as e:
            print('ERROR: DNS lookup failed:', e)
        else:
            self.session = Session(account)
            print('Routes:', routes)
            # Use an MSRP chat stream for the session
            self.chat_stream = ChatStream()
            self.session.connect(self.callee, routes, streams=[self.chat_stream])

    def _NH_SIPSessionGotRingIndication(self, notification):
        print('Callback: ringing')

    def _NH_SIPSessionDidStart(self, notification):
        print('Callback: MSRP session started')
        try:
            self.chat_stream = notification.data.streams[0]
            print('MSRP session established. You can now send messages.')
        except Exception as e:
            print('Error:', e)

    def _NH_ChatStreamGotMessage(self, notification):
        # Extract and display the content of the incoming message as a string (no decoding)
        try:
            message_content = notification.data.message.content
            print(f'New message received: {message_content}')
        except Exception as e:
            print(f'Failed to handle incoming message: {e}')

    def send_message(self, message):
        if self.chat_stream:
            self.chat_stream.send_message(message)
            print(f'Message sent: {message}')
        else:
            print('MSRP session not established yet.')

    def _NH_SIPSessionDidFail(self, notification):
        print('Callback: failed to connect')
        try:
            print(notification.data.code, notification.data.reason)
        except:
            print(notification)
        self.stop()

    def _NH_SIPSessionDidEnd(self, notification):
        print('Callback: session ended')
        self.stop()

    def _NH_SIPApplicationDidEnd(self, notification):
        print('Callback: application ended')
        self.ended.set()

# place an MSRP call to the specified SIP URI
application = SimpleMSRPApplication()
application.call(TARGET_URI)

# Main loop to send MSRP messages
try:
    while True:
        message = input('Enter message (or type "quit" to exit): ')
        if message.lower() == "quit":
            break
        application.send_message(message)
except KeyboardInterrupt:
    print('Interrupted. Exiting...')
finally:
    try:
        if application.session:
            application.session.end()
        application.ended.wait()
    except Exception as e:
        print('ERROR:', e)
