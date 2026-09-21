// Generated from packages/contracts/src/chat.ts; SHA256 ec07bf2d0fdda52b4a398330db095911b0891eeafde5cdf121ec0d15ee19fb13. Do not edit.
import type { SseEvent } from './sse';

export interface Source { kind: 'product'|'knowledge'|'price_rule'; source_id: string; title: string; excerpt: string; source: string }
export interface QuoteLine {
  quote_item_id: string; product_id: string; sku: string; name_tr: string; quantity: number;
  unit_price_try: string; gross_total_try: string; discount_total_try: string; net_total_try: string;
  rule_ids: string[]; status: string; fulfillment_status: string; replaced_by: string|null;
}
export interface Quote {
  quote_id: string; customer_id: string; customer_name: string; status: string; currency: string; version: number;
  items: QuoteLine[]; history: QuoteLine[]; gross_total_try: string; discount_total_try: string; net_total_try: string; rule_ids: string[];
}
export type Mode = 'fallback'|'deterministic';
export type ToolName = 'search_products'|'get_knowledge_entries'|'get_quote'|'add_to_quote'|'update_quote_item'|'replace_with_alternative';
interface Payloads {
  message_start: {mode: Mode};
  tool_call_start: {name: ToolName; input: Record<string,unknown>; tool_sequence: number; action_index: number};
  tool_call_result: {name: ToolName; tool_sequence: number; success: boolean; output: Record<string,unknown>; sources: Source[]; replayed: boolean; mutation_applied: boolean};
  sources: {sources: Source[]};
  text_delta: {text: string};
  done: {success: true; quote_id: string; quote_version: number; mode: Mode; source_ids: string[]};
  error: {code: string; detail: string; retryable: boolean; committed: boolean; quote_id: string};
}
export type EventType=keyof Payloads;
export type ChatEvent = {[K in EventType]: {schema_version:1;session_id:string;message_id:string;attempt_id:string;event_seq:number;type:K;payload:Payloads[K]}}[EventType];
const names = new Set(['search_products','get_knowledge_entries','get_quote','add_to_quote','update_quote_item','replace_with_alternative']);
const record=(v:unknown):v is Record<string,unknown> => typeof v==='object' && v!==null && !Array.isArray(v);
const strings=(v:unknown):v is string[] => Array.isArray(v) && v.every(x=>typeof x==='string');
const positive=(v:unknown):v is number => typeof v==='number' && Number.isSafeInteger(v) && v>0;
const sourceList=(v:unknown):v is Source[] => Array.isArray(v) && v.every(s=>record(s) && ['product','knowledge','price_rule'].includes(String(s.kind)) && ['source_id','title','excerpt','source'].every(k=>typeof s[k]==='string'));
const mode=(v:unknown):v is Mode => v==='fallback'||v==='deterministic';

export function parseChatEvent(wire:SseEvent):ChatEvent {
  const e:unknown=JSON.parse(wire.data);
  if (!record(e) || e.schema_version!==1 || !['session_id','message_id','attempt_id'].every(k=>typeof e[k]==='string' && e[k]!=='' ) || !positive(e.event_seq) || e.type!==wire.event || !record(e.payload)) throw new Error('Geçersiz sohbet olayı.');
  const p=e.payload;
  let valid=false;
  switch(e.type){
    case 'message_start': valid=mode(p.mode);break;
    case 'tool_call_start': valid=names.has(String(p.name)) && record(p.input) && positive(p.tool_sequence) && typeof p.action_index==='number' && Number.isSafeInteger(p.action_index) && p.action_index>=0;break;
    case 'tool_call_result': valid=names.has(String(p.name)) && positive(p.tool_sequence) && typeof p.success==='boolean' && record(p.output) && sourceList(p.sources) && typeof p.replayed==='boolean' && typeof p.mutation_applied==='boolean' && !(p.replayed && p.mutation_applied);break;
    case 'sources': valid=sourceList(p.sources);break;
    case 'text_delta': valid=typeof p.text==='string';break;
    case 'done': valid=p.success===true && typeof p.quote_id==='string' && positive(p.quote_version) && mode(p.mode) && strings(p.source_ids);break;
    case 'error': valid=typeof p.code==='string' && typeof p.detail==='string' && typeof p.quote_id==='string' && typeof p.retryable==='boolean' && typeof p.committed==='boolean';break;
  }
  if(!valid) throw new Error('Geçersiz sohbet olay içeriği.');
  return e as ChatEvent;
}

export interface StreamState {
  sessionId:string; messageId:string; attemptId?:string; lastSeq:number;
  text:string; sources:Source[]; status:'connecting'|'streaming'|'done'|'error'; error?:string; needsRefetch:boolean;
}
export function initialStream(sessionId:string,messageId:string):StreamState {
  return {sessionId,messageId,lastSeq:0,text:'',sources:[],status:'connecting',needsRefetch:false};
}
/** No client-side quantity/price math. Replay and done cause a canonical GET instead. */
export function reduceChatEvent(state:StreamState,event:ChatEvent):StreamState {
  if(event.session_id!==state.sessionId || event.message_id!==state.messageId) throw new Error('Sohbet bağlamı eşleşmiyor.');
  if(state.attemptId && event.attempt_id!==state.attemptId) throw new Error('Akış denemesi eşleşmiyor.');
  if(event.event_seq<=state.lastSeq) return state;
  if(event.event_seq!==state.lastSeq+1 || (!state.attemptId && event.type!=='message_start') || state.status==='done' || state.status==='error') throw new Error('Akış sırası geçersiz.');
  const next={...state,attemptId:event.attempt_id,lastSeq:event.event_seq};
  switch(event.type){
    case 'message_start': return {...next,status:'streaming'};
    case 'text_delta': return {...next,text:next.text+event.payload.text};
    case 'sources': return {...next,sources:event.payload.sources};
    case 'tool_call_result': return {...next,needsRefetch:next.needsRefetch||event.payload.mutation_applied||event.payload.replayed};
    case 'done': return {...next,status:'done',needsRefetch:true};
    case 'error': return {...next,status:'error',error:event.payload.detail,needsRefetch:next.needsRefetch||event.payload.committed};
    default:return next;
  }
}
