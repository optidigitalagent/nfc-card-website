"""Production transport contracts. Disabled by default and absent from the preview.

The owner must separately authorize live transport verification. No environment
values are read here. Dependencies are passed explicitly from a future serverless host.
"""
import json

class TelegramAdapter:
    def __init__(self,token,chat_id,transport,*,authorized=False):
        self._token=token;self._chat=chat_id;self._transport=transport;self._authorized=authorized
    def send(self,lead_id,message):
        if not self._authorized:raise RuntimeError('LIVE_NOTIFICATIONS_NOT_AUTHORIZED')
        # transport must implement timeout, no retries, redacted errors, HTTPS only.
        result=self._transport.post_json('https://api.telegram.org/bot'+self._token+'/sendMessage',
            {'chat_id':self._chat,'text':message,'disable_web_page_preview':True},timeout=8)
        if not isinstance(result,dict) or result.get('ok') is not True:raise RuntimeError('telegram_not_accepted')
        return 'accepted'

class EmailAdapter:
    def __init__(self,recipient,transport,*,authorized=False):
        self._recipient=recipient;self._transport=transport;self._authorized=authorized
    def send(self,lead_id,message):
        if not self._authorized:raise RuntimeError('LIVE_NOTIFICATIONS_NOT_AUTHORIZED')
        if not self._transport.send_text(to=self._recipient,subject=f'NFC CARD {lead_id}',body=message,timeout=8):
            raise RuntimeError('email_not_accepted')
        return 'accepted'
