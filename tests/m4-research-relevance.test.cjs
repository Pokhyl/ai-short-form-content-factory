const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M4-Research.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function runCode(name,{input=[],nodes={}}={}){
  const code=byName[name].parameters.jsCode;
  const $input={
    first:()=>({json:input[0]??{}}),
    all:()=>input.map((json)=>({json})),
  };
  const $=(nodeName)=>({
    all:()=> (nodes[nodeName]??[]).map((json)=>({json})),
    first:()=>({json:(nodes[nodeName]??[])[0]??{}}),
  });
  return new Function('$input','$',code)($input,$);
}

test('M4 builds subject-focused local and encyclopedia queries for all supported languages',()=>{
  const cases=[
    ['uk','як працює барометр','барометр'],
    ['ru','как работает термос','термос'],
    ['pl','jak działa lodówka','lodówka'],
    ['en','how a bicycle brake works','bicycle brake'],
  ];
  for(const [language,topic,subject] of cases){
    const rows=runCode('Build Search Queries',{input:[{
      topic,language_code:language,research_run_id:'12345678-1234-4234-8234-123456789012',
    }]}).map((item)=>item.json);
    assert.equal(rows.length,3);
    assert.equal(rows[0].subject,subject);
    assert.equal(rows[1].query_kind,'subject_principle');
    assert.match(rows[1].search_query,new RegExp(subject.split(' ').join('.*'),'iu'));
    assert.equal(rows[2].query_kind,'encyclopedia');
    assert.equal(rows[2].search_engine,'wikipedia');
  }
});

test('M4 search-result relevance gate rejects unrelated SEO pages before evidence fetch',()=>{
  const q={
    research_run_id:'12345678-1234-4234-8234-123456789012',
    topic:'як працює барометр',
    language_code:'uk',
    subject:'барометр',
    subject_tokens:['барометр'],
    search_query:'як працює барометр',
    query_kind:'primary_local',
    query_index:1,
  };
  const result=runCode('Build Fetch Candidates',{
    input:[{results:[
      {url:'https://example.com/keyword-tool',title:'Keyword Finder',content:'Пошук і аналіз ключових слів'},
      {url:'https://science.example/barometry',title:'Як працюють барометри',content:'Барометр вимірює атмосферний тиск.'},
    ]}],
    nodes:{'Build Search Queries':[q]},
  });
  assert.equal(result.length,1);
  assert.equal(result[0].json.source_domain,'science.example');
  assert.equal(result[0].json.candidate_valid,true);
});

test('M4 relevance gate tolerates normal inflection but not unrelated same-language text',()=>{
  const q={
    research_run_id:'12345678-1234-4234-8234-123456789012',
    topic:'jak działa lodówka',
    language_code:'pl',
    subject:'lodówka',
    subject_tokens:['lodówka'],
    search_query:'jak działa lodówka',
    query_kind:'primary_local',
    query_index:1,
  };
  const result=runCode('Build Fetch Candidates',{
    input:[{results:[
      {url:'https://shop.example/promocje',title:'Najlepsze promocje',content:'Elektronika i sprzęt domowy'},
      {url:'https://edu.example/lodowki',title:'Budowa lodówki',content:'Zasada działania lodówek i obieg czynnika chłodniczego.'},
    ]}],
    nodes:{'Build Search Queries':[q]},
  });
  assert.equal(result.length,1);
  assert.equal(result[0].json.source_domain,'edu.example');
});
