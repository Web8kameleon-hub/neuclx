import test from 'node:test';import assert from 'node:assert/strict';import{datum,EvidenceState,jonaDecision}from'../src/index.js';
test('unavailable cannot hide a value',()=>assert.throws(()=>datum(42,EvidenceState.UNAVAILABLE)));
test('declared output stays in JONA sandbox',()=>assert.equal(jonaDecision(datum('future',EvidenceState.DECLARED)),'sandbox_only'));
test('measured output requires provenance',()=>assert.throws(()=>datum(1,EvidenceState.MEASURED,{method:'meter'})));
