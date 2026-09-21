import assert from 'node:assert/strict';
import test from 'node:test';
import {createSseParser,parseChatEvent,initialStream,reduceChatEvent,type ChatEvent} from '../src/index';
const envelope=(type:string,seq:number,payload:unknown)=>({schema_version:1,session_id:'session',message_id:'message',attempt_id:'attempt',event_seq:seq,type,payload});
const parse=(e:ReturnType<typeof envelope>)=>parseChatEvent({event:e.type,data:JSON.stringify(e)});

test('actual envelope survives every UTF-8 split and reducer completes once',()=>{
 const events=[envelope('message_start',1,{mode:'fallback'}),envelope('text_delta',2,{text:'Bağlantı ğüşİöç'}),envelope('done',3,{success:true,quote_id:'quote',quote_version:2,mode:'fallback',source_ids:[]})];
 const bytes=new TextEncoder().encode(events.map(e=>`event: ${e.type}\r\ndata: ${JSON.stringify(e)}\r\n\r\n`).join(''));
 for(let split=0;split<=bytes.length;split++){
   const parser=createSseParser();
   const frames=[...parser.push(bytes.slice(0,split)),...parser.push(bytes.slice(split)),...parser.finish()];
   const state=frames.map(parseChatEvent).reduce(reduceChatEvent,initialStream('session','message'));
   assert.equal(state.text,'Bağlantı ğüşİöç');assert.equal(state.status,'done');assert.equal(state.needsRefetch,true);assert.equal(state.lastSeq,3);
 }
});

test('replayed delta is never applied locally and duplicate event is ignored',()=>{
 const start=parse(envelope('message_start',1,{mode:'fallback'}));
 const replay=parse(envelope('tool_call_result',2,{name:'add_to_quote',tool_sequence:1,success:true,output:{delta:{quantity:99}},sources:[],replayed:true,mutation_applied:false}));
 const state=reduceChatEvent(reduceChatEvent(initialStream('session','message'),start),replay);
 assert.equal(state.needsRefetch,true);assert.equal(state.text,'');assert.equal('quantity' in state,false);
 assert.strictEqual(reduceChatEvent(state,replay),state);
});

test('error preserves partial text and signals committed-state refetch',()=>{
 let state=reduceChatEvent(initialStream('session','message'),parse(envelope('message_start',1,{mode:'fallback'})));
 state=reduceChatEvent(state,parse(envelope('text_delta',2,{text:'Kısmi yanıt'})));
 state=reduceChatEvent(state,parse(envelope('error',3,{code:'INTERNAL_ERROR',detail:'Tekrar dene',retryable:true,committed:true,quote_id:'quote'})));
 assert.equal(state.text,'Kısmi yanıt');assert.equal(state.status,'error');assert.equal(state.error,'Tekrar dene');assert.equal(state.needsRefetch,true);
 assert.throws(()=>reduceChatEvent(state,parse(envelope('text_delta',4,{text:'sonra'}))),/sırası/);
});

test('unknown schema, mismatched type, impossible receipt flags and broken order rejected',()=>{
 assert.throws(()=>parseChatEvent({event:'text_delta',data:JSON.stringify(envelope('done',1,{}))}));
 assert.throws(()=>parse({...envelope('text_delta',1,{text:'a'}),schema_version:2}));
 assert.throws(()=>parse(envelope('tool_call_result',1,{name:'add_to_quote',tool_sequence:1,success:true,output:{},sources:[],replayed:true,mutation_applied:true})));
 assert.throws(()=>parse(envelope('unknown',1,{})));
 const start=parse(envelope('message_start',1,{mode:'fallback'}));
 const state=reduceChatEvent(initialStream('session','message'),start);
 assert.throws(()=>reduceChatEvent(state,parse(envelope('text_delta',3,{text:'gap'}))));
 assert.throws(()=>reduceChatEvent(state,{...parse(envelope('text_delta',2,{text:'x'})),session_id:'other'} as ChatEvent));
 assert.throws(()=>reduceChatEvent(state,{...parse(envelope('text_delta',2,{text:'x'})),attempt_id:'other'} as ChatEvent));
});
