#!/usr/bin/python

from application.notification import NotificationCenter
from sipsimple.account import AccountManager
from sipsimple.application import SIPApplication
from sipsimple.core import SIPURI, ToHeader
from sipsimple.lookup import DNSLookup, DNSLookupError
from sipsimple.storage import FileStorage
from sipsimple.session import Session
from sipsimple.streams import MediaStreamRegistry
from sipsimple.threading.green import run_in_green_thread
from threading import Event

CALLER_ACCOUNT  = 'andriy.makukha@sip2sip.info'             # must be configured in config/config
TARGET_URI      = 'sip:________@sip.linphone.org'           # SIP URI we want to call

class SimpleCallApplication(SIPApplication):

    def __init__(self):
        SIPApplication.__init__(self)
        self.ended = Event()
        self.callee = None
        self.session = None
        notification_center = NotificationCenter()
        notification_center.add_observer(self)

    def call(self, callee):
        print 'Placing call to', callee
        self.callee = callee
        self.start(FileStorage('config'))

    @run_in_green_thread
    def _NH_SIPApplicationDidStart(self, notification):
        print 'Callback: application started'
        self.callee = ToHeader(SIPURI.parse(self.callee))
        # Retrieve account from config
        try:
            account = AccountManager().get_account(CALLER_ACCOUNT)
            host = account.sip.outbound_proxy.host
            port = account.sip.outbound_proxy.port
            transport = account.sip.outbound_proxy.transport
            print '      Host = %s\n      Port = %s\n Transport = %s' % (host, port, transport)
        except Exception, e:
            print 'ERROR:', e
        try:
            uri = SIPURI(host=host, port=port, parameters={'transport': transport})
            routes = DNSLookup().lookup_sip_proxy(uri, ['tcp', 'udp']).wait()
        except DNSLookupError, e:
            print 'ERROR: DNS lookup failed:', e
        else:
            self.session = Session(account)
            print 'Routes:', routes
            self.session.connect(self.callee, routes, streams=[MediaStreamRegistry.AudioStream()])

    def _NH_SIPSessionGotRingIndication(self, notification):
        print 'Callback: ringing'

    def _NH_SIPSessionDidStart(self, notification):
        print 'Callback: session started'
        try:
            audio_stream = notification.data.streams[0]
            print 'Audio session established using "%s" codec at %sHz' % (audio_stream.codec, audio_stream.sample_rate)
        except:
            print notification

    def _NH_SIPSessionDidFail(self, notification):
        print 'Callback: failed to connect'
        try:
            print notification.data.code, notification.data.reason
        except:
            print notification
        self.stop()

    def _NH_SIPSessionDidEnd(self, notification):
        print 'Callback: session ended'
        self.stop()

    def _NH_SIPApplicationDidEnd(self, notification):
        print 'Callback: application ended'
        self.ended.set()

# place an audio call to the specified SIP URI
application = SimpleCallApplication()
application.call(TARGET_URI)
raw_input('Press Enter to exit\n\n')
try:
    application.session.end()
    application.ended.wait()
except Exception, e:
    print 'ERROR:', e
