import assert from 'node:assert/strict';
import test from 'node:test';
import { initialStream, type Source } from '@tbr/contracts';
import { visibleAttemptContent } from '../src/api/retry';

test('retry preserves previous text and citations through reconnect and early error', () => {
  const source: Source = {kind:'knowledge',source_id:'K-1',title:'İade',excerpt:'Önceki kaynak',source:'demo'};
  const previous = {text:'Önceki kısmi yanıt',sources:[source]};
  for (const status of ['connecting','streaming','error'] as const) {
    const next = {...previous,...visibleAttemptContent({...initialStream('s','m'),status})};
    assert.deepEqual(next, previous);
  }
});
test('retry replaces rather than duplicates text and uses new citations; successful empty answer clears old content', () => {
  const previous = {text:'Önceki yanıt',sources:[{kind:'knowledge',source_id:'K-1',title:'Eski',excerpt:'Eski',source:'demo'}]};
  const state = {...initialStream('s','m'),text:'Yeni parça',status:'streaming' as const};
  assert.deepEqual({...previous,...visibleAttemptContent(state)}, {text:'Yeni parça',sources:[]});
  assert.deepEqual({...previous,...visibleAttemptContent({...state,text:'Yeni parça devam',status:'error'})}, {text:'Yeni parça devam',sources:[]});
  assert.deepEqual({...previous,...visibleAttemptContent({...state,text:'',status:'done'})}, {text:'',sources:[]});
});
