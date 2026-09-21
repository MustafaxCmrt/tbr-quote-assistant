import assert from 'node:assert/strict';
import test from 'node:test';
import {acceptQuote} from '../src/api/state';

test('late poll cannot replace new version or changed quote context',()=>{
 const current={quote_id:'Q-A',version:8,total:'50.00'};
 assert.strictEqual(acceptQuote(current,{quote_id:'Q-A',version:7,total:'30.00'},'Q-A'),current);
 assert.strictEqual(acceptQuote(current,{quote_id:'Q-B',version:99,total:'90.00'},'Q-A'),current);
 const newer={quote_id:'Q-A',version:9,total:'70.00'};
 assert.strictEqual(acceptQuote(current,newer,'Q-A'),newer);
 const selected={quote_id:'Q-B',version:1,total:'10.00'};
 assert.strictEqual(acceptQuote(current,selected,'Q-B'),selected);
 assert.equal(acceptQuote(null,current,'Q-B'),null);
});
