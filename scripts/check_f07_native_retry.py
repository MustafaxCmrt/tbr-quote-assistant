"""Read-only snapshot check of Mustafa's physical iPhone retry, not a seed test."""
import json
from urllib.request import urlopen


def read(path):
    with urlopen("http://127.0.0.1:8001" + path, timeout=10) as response:
        return json.load(response)


quote = read('/api/quotes/Q-1001')
assert quote['version'] == 2
line = next(x for x in quote['items'] if x['product_id'] == 'PRD-BC-110')
assert line['quantity'] == 2
assert quote['net_total_try'] == '15980.00'
sessions = read('/api/chat/sessions?quote_id=Q-1001')
mutations = []
for session in sessions:
    if session['channel'] == 'mobile':
        mutations += [x for x in read('/api/tool-calls?session_id=' + session['session_id'])
                      if x['tool_name'] == 'add_to_quote'
                      and x['message_id'] == '29092b9a-ed3f-48a1-ba64-11143e9c42b7']
assert len(mutations) == 2
assert len({x['attempt_id'] for x in mutations}) == 2
assert sum(x['mutation_applied'] for x in mutations) == 1
assert sum(x['replayed'] for x in mutations) == 1
assert all(x['mutation_applied'] != x['replayed'] for x in mutations)
print('PASS Q-1001 version2 quantity2 net15980.00 unchanged after physical retry')
print('PASS same message_id, two distinct attempts, one actual mutation and one receipt replay')
for x in mutations:
    print(json.dumps({k:x[k] for k in ['message_id','attempt_id','replayed','mutation_applied']}))
