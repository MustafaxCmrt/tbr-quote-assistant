"""Observe real curl -N frame arrival, including the web proxy. No quote mutation."""
import json
import subprocess
import time
from urllib.request import Request, urlopen
from uuid import uuid4

for base in ['http://127.0.0.1:8001','http://127.0.0.1:5173']:
    with urlopen(Request(base+'/api/chat/sessions',data=json.dumps({'customer_id':'CUST-IST-001','quote_id':'Q-1001'}).encode(),headers={'Content-Type':'application/json'}),timeout=10) as response:
        session=json.load(response)['session_id']
    body=json.dumps({'session_id':session,'quote_id':'Q-1001','message_id':uuid4().hex,'message':'İade süresi nedir ve teklifimde hangi ürün var?'})
    command=['curl','-N','--silent','--show-error','--fail','--max-time','15','-H','Content-Type: application/json','-d',body,base+'/api/chat/stream']
    print('curl -N POST',base+'/api/chat/stream')
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    start=time.monotonic();events=[];times=[]
    for line in process.stdout:
        if line.startswith('data: '):
            event=json.loads(line[6:]);events.append(event)
            elapsed=time.monotonic()-start
            print(f'{elapsed:.3f}s {event["type"]} seq={event["event_seq"]}')
            if event['type']=='text_delta':times.append(elapsed)
    _,error=process.communicate();assert process.returncode==0,error
    assert events[0]['type']=='message_start' and events[-1]['type']=='done'
    assert len(times)>2 and times[-1]-times[0]>0.02, 'Frames buffered instead of incremental'
    assert [e['event_seq'] for e in events]==list(range(1,len(events)+1))
    print(f'PASS incremental template stream: {len(times)} text chunks over {times[-1]-times[0]:.3f}s; curl exit 0')
