import assert from 'node:assert/strict';
import test from 'node:test';
import type { Quote } from '@tbr/contracts';
import { acceptQuote } from '../src/api/state';

test('mobile canonical quote ignores stale versions and responses from another selection',()=>{
  const current:Quote={quote_id:'Q-A',customer_id:'C-A',customer_name:'Demo',status:'draft',currency:'TRY',version:8,items:[],history:[],gross_total_try:'50.00',discount_total_try:'0.00',net_total_try:'50.00',rule_ids:[]};
  assert.strictEqual(acceptQuote(current,{...current,version:7,net_total_try:'30.00'},'Q-A'),current);
  assert.strictEqual(acceptQuote(current,{...current,quote_id:'Q-B',version:99},'Q-A'),current);
  const newer={...current,version:9,net_total_try:'70.00'};
  assert.strictEqual(acceptQuote(current,newer,'Q-A'),newer);
  const other={...current,quote_id:'Q-B',version:1};
  assert.strictEqual(acceptQuote(current,other,'Q-B'),other);
  assert.equal(acceptQuote(null,current,'Q-B'),null);
});
