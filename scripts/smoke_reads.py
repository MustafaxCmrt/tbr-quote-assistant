"""Real HTTP read-tool smoke against the local Compose API."""
import json
from urllib.request import Request, urlopen

base = 'http://127.0.0.1:8001'

def request(path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    with urlopen(Request(base+path,data=payload,headers={'Content-Type':'application/json'}),timeout=5) as response:
        assert response.status==200
        return json.load(response)

products = request('/api/tools/search_products', {'query':'kablosuz QR okuyucu','filters':{'max_price_try':8500}})
assert [row['product_id'] for row in products['recommendations']]==['PRD-BC-110']
assert products['recommendations'][0]['price_try']=='7990.00'
policy = request('/api/tools/get_knowledge_entries', {'query':'iade','topic':'return_policy'})
assert {row['knowledge_id'] for row in policy['entries']}=={'KNE-RET-001','KNE-RET-001-SUP'}
quote = request('/api/quotes/Q-2003')
assert quote['net_total_try']=='4211.20'
assert quote['rule_ids']==['RUL-PLUS-QTY']
print('PASS real HTTP: hard-filtered product, base + SUP policy, canonical snapshot quote with Decimal totals')
