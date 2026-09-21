"""Read-only real HTTP chat smoke; creates a session, never changes quote items."""
import json
from urllib.request import Request, urlopen
from uuid import uuid4

base = 'http://127.0.0.1:8001'

def call(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    with urlopen(Request(base + path, data=data, headers={'Content-Type':'application/json'}), timeout=15) as response:
        return json.load(response)

before = call('/api/quotes/Q-1001')
session = call('/api/chat/sessions', {'customer_id':'CUST-IST-001','quote_id':'Q-1001','channel':'web'})
result = call('/api/chat', {'session_id':session['session_id'],'message_id':uuid4().hex,'quote_id':'Q-1001','message':'İade süresi nedir ve teklifimde hangi ürün var?'})
assert result['mode'] == 'fallback' and result['provider_calls'] == 0
assert {'KNE-RET-001','KNE-FALL-001','PRD-BC-110'} <= {s['source_id'] for s in result['sources']}
assert call('/api/quotes/Q-1001') == before
print('PASS real HTTP chat: sourced Turkish fallback, zero provider calls, unchanged persisted quote')
