const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

function sentenceCounter(name){
  const src=byName[name].parameters.jsCode;
  const start=src.indexOf('function countNaturalCompleteSentences');
  const end=src.indexOf('const naturalCompleteSentenceCount',start);
  assert.ok(start>=0 && end>start,name+' sentence helper missing');
  return new Function(src.slice(start,end)+';return countNaturalCompleteSentences;')();
}

for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2']){
  test(name+': standalone closure filler does not count as a third content sentence',()=>{
    const count=sentenceCounter(name);
    assert.equal(count('Pierwsze zdanie jest pełne. Drugie zdanie też jest pełne. Koniec.'),2);
    assert.equal(count('Pierwsze zdanie jest pełne. Drugie zdanie też jest pełne. Trzecie zdanie również jest pełne.'),3);
    assert.equal(count('First sentence is complete. Second sentence is complete. The end.'),2);
    assert.equal(count('Первое предложение полное. Второе предложение полное. Конец.'),2);
    assert.equal(count('Перше речення повне. Друге речення повне. Кінець.'),2);
  });
}

test('Build Script Prompt applies the three-content-sentence contract to every 30+ second language',()=>{
  const src=byName['Build Script Prompt'].parameters.jsCode;
  assert.match(src,/duration >= 30/);
  assert.match(src,/at least 3 natural complete content sentences in every output language/);
  assert.match(src,/Koniec\., The end\., Конец\., or Кінець\./);
});

for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
  test(name+': repair always preserves the sentence contract and exact 30s final-scene minimum',()=>{
    const src=byName[name].parameters.jsCode;
    assert.match(src,/joined narration MUST contain at least three natural complete content sentences regardless of the current validation error/);
    assert.match(src,/index === candidateObject\.scenes\.length - 1 && Number\(ctx\.target_duration_seconds\) === 30 \? 6 : 2/);
    assert.match(src,/valid:words>=minimum/);
  });
}
