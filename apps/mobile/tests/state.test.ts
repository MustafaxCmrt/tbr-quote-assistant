import assert from 'node:assert/strict';
import test from 'node:test';
import type { Quote } from '@tbr/contracts';
import { acceptQuote, isQuote } from '../src/api/state';

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

test('mobile rejects a quote payload whose shape the screens cannot render',()=>{
  const valid:Quote={quote_id:'Q-A',customer_id:'C-A',customer_name:'Demo',status:'draft',currency:'TRY',version:1,items:[],history:[],gross_total_try:'0.00',discount_total_try:'0.00',net_total_try:'0.00',rule_ids:[]};
  assert.equal(isQuote(valid),true);
  for (const broken of [null,[],{...valid,items:undefined},{...valid,history:{}},{...valid,version:'1'},{...valid,rule_ids:[1]},{...valid,net_total_try:12},{...valid,items:[{product_id:'P'}]}])
    assert.equal(isQuote(broken),false,JSON.stringify(broken));
  const line={quote_item_id:'I',product_id:'P',sku:'S',name_tr:'Ürün',quantity:1,unit_price_try:'1.00',gross_total_try:'1.00',discount_total_try:'0.00',net_total_try:'1.00',rule_ids:[],status:'active',fulfillment_status:'in_stock',replaced_by:null};
  assert.equal(isQuote({...valid,items:[line],history:[{...line,status:'replaced',replaced_by:'J'}]}),true);
});
