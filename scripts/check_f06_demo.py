"""Read-only verification of records created through the F06 browser smoke."""
import json
from urllib.request import Request, urlopen


def read(path, body=None):
    req = Request(
        'http://127.0.0.1:8001' + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'},
    )
    with urlopen(req, timeout=10) as response:
        return json.load(response)


quote = read('/api/quotes/Q-1002')
assert quote['version'] == 2
assert len(quote['items']) == 1
assert quote['items'][0]['product_id'] == 'PRD-30F871664B134D10'
assert quote['items'][0]['quantity'] == 1
assert quote['net_total_try'] == '1234.50'
print('PASS browser and canonical API: Q-1002, version 2, quantity 1, net 1234.50')
knowledge = read('/api/tools/get_knowledge_entries', {'query': 'demo', 'topic': 'demo_training'})
assert any(x['knowledge_id'] == 'KNE-32FFB1FD0CFD485B' for x in knowledge['entries'])
print('PASS UI-created knowledge visible through real retrieval tool')
sessions = read('/api/chat/sessions?quote_id=Q-1002')
logs = read('/api/tool-calls?session_id=' + sessions[0]['session_id'])
mutations = [x for x in logs if x['tool_name'] == 'add_to_quote']
assert len(mutations) == 2
assert mutations[0]['mutation_applied'] and not mutations[0]['replayed']
assert mutations[1]['replayed'] and not mutations[1]['mutation_applied']
assert mutations[0]['message_id'] == mutations[1]['message_id']
assert mutations[0]['attempt_id'] != mutations[1]['attempt_id']
print('PASS actual wrapper retry: same message, distinct attempts, one applied mutation')
