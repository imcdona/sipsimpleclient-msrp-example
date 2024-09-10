# SIP SIMPLE client example

This is a small example of establishing a VoIP call with SIP in Python. It corrects some errors of the [official SIP SIMPLE library example](http://sipsimpleclient.org/projects/sipsimpleclient/wiki/SipDeveloperGuide).

### Install dependencies
http://sipsimpleclient.org/projects/sipsimpleclient/wiki/SipDeveloperGuide

### Configure

 - Change file config/config entering your account credentials and SIP proxy
 - Change constant `CALLER_ACCOUNT` in sample.py to match the account in config/config
 - Change constant `TARGET_URI` in sample.py to contain callee's SIP URI

### Running

Voice call
```sh
python sample.py
```

MSRP Chat Session
```sh
python3 msrp-chat.py
```
