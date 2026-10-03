const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodes=w.nodes.filter(n=>n.parameters?.jsCode?.includes('function canonicalizeTransientPhotoActionIntent'));
const fn=n=>{const c=n.parameters.jsCode,start=c.indexOf('function canonicalizeTransientPhotoActionIntent'),end=c.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);return new Function(c.slice(start,end)+';return canonicalizeTransientPhotoActionIntent;')();};
test('12015 impersonal piercing becomes static co-presence without dropping any object',()=>{
 assert.equal(nodes.length,4);
 for(const n of nodes) assert.equal(fn(n)(['metal staples','paper sheets'],'Metal staple piercing through a stack of paper sheets'),'A clear photo of metal staples with paper sheets.',n.name);
});
test('piercing generalizes to other mechanical objects',()=>{
 for(const n of nodes) assert.equal(fn(n)(['needle','fabric'],'A needle piercing fabric'),'A clear photo of needle with fabric.',n.name);
});
test('explicit human piercing action stays authored',()=>{
 for(const n of nodes) for(const intent of ['A worker piercing metal with a drill','Hands piercing paper with a needle']) assert.equal(fn(n)(['needle','paper'],intent),intent,n.name);
});
test('static penetrated state and unrelated actions remain unchanged',()=>{
 for(const n of nodes) for(const intent of ['A needle protruding through fabric','A drill beside metal sheets']) assert.equal(fn(n)(['needle','fabric'],intent),intent,n.name);
});
