const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M4-Research.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function runCode(name,{input=[],nodes={},json=input[0]??{},itemIndex=0}={}){
  const code=byName[name].parameters.jsCode;
  const $input={
    first:()=>({json:input[0]??{}}),
    all:()=>input.map((row)=>({json:row})),
  };
  const $=(nodeName)=>({
    all:()=> (nodes[nodeName]??[]).map((row)=>({json:row})),
    first:()=>({json:(nodes[nodeName]??[])[0]??{}}),
  });
  return new Function('$input','$','$json','$itemIndex',code)(
    $input,$,json,itemIndex
  );
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

test('M4 disambiguates an unqualified theory using explanatory evidence across output languages',()=>{
  const cases=[
    ['uk','теория большого взрыва','научная теория'],
    ['pl','teoria ewolucji','teoria naukowa'],
    ['en','theory of evolution','scientific theory'],
  ];
  for(const [language,topic,scientificTerm] of cases){
    const queries=runCode('Build Search Queries',{input:[{
      topic,language_code:language,research_run_id:'12345678-1234-4234-8234-123456789012',
    }]}).map((item)=>item.json);
    assert.equal(queries[1].explain_theory,true);
    assert.ok(queries[1].search_query.includes(scientificTerm));
    assert.equal(queries[1].search_engine,'duckduckgo');
    const results=runCode('Build Fetch Candidates',{
      input:[
        {results:[{url:'https://media.example/show',title:topic+' сериал',content:'телесериал про друзей'}]},
        {results:[
          {url:'https://science.example/article',title:topic+' объяснение',content:'теория подтверждается исследованиями'},
          {url:'https://university.example/lecture',title:topic+' научная теория',content:'научное объяснение'},
          {url:'https://museum.example/exhibit',title:topic+' факты',content:'объяснение явления'},
        ]},
        {results:[]},
      ],nodes:{'Build Search Queries':queries},
    }).map((item)=>item.json);
    assert.ok(results.length>=3);
    assert.ok(results.every((item)=>item.query_kind==='subject_principle'));
    assert.ok(results.every((item)=>item.source_domain!=='media.example'));
  }
});

test('M4 fails closed when theory search has only a namesake show, and respects explicit show intent',()=>{
  const context={research_run_id:'12345678-1234-4234-8234-123456789012',language_code:'ru'};
  const scientific=runCode('Build Search Queries',{input:[{...context,topic:'теория большого взрыва'}]}).map((i)=>i.json);
  const show={url:'https://media.example/show',title:'Теория большого взрыва сериал',content:'ситком и актеры'};
  const onlyShow=runCode('Build Fetch Candidates',{
    input:[{results:[show]},{results:[]},{results:[]}],nodes:{'Build Search Queries':scientific},
  });
  assert.equal(onlyShow[0].json.candidate_valid,false);
  const explicit=runCode('Build Search Queries',{input:[{...context,topic:'сериал теория большого взрыва'}]}).map((i)=>i.json);
  assert.equal(explicit[1].explain_theory,false);
  const showSources=runCode('Build Fetch Candidates',{
    input:[{results:[show]},{results:[]},{results:[]}],nodes:{'Build Search Queries':explicit},
  });
  assert.equal(showSources[0].json.candidate_valid,true);
});

test('M4 evidence normalization resolves the active retry candidate by item index instead of fragile paired-item ancestry',()=>{
  const candidate={
    research_run_id:'12345678-1234-4234-8234-123456789012',
    search_query:'jak działa lidar',
    search_rank:1,
    search_engines:['duckduckgo'],
    source_url:'https://science.example/lidar',
    canonical_url:'https://science.example/lidar',
    source_domain:'science.example',
    title:'LiDAR',
    snippet:'Pomiar odległości światłem.',
    candidate_valid:true,
  };
  const fetch={
    statusCode:200,
    headers:{'content-type':'text/html; charset=utf-8'},
  };
  const extracted={
    page_title:'Jak działa LiDAR',
    body_text:'LiDAR mierzy czas powrotu impulsu światła.',
  };

  for(const activeNode of [
    'Build Fetch Candidates',
    'Build Fetch Candidates Retry 1',
    'Build Fetch Candidates Retry 2',
  ]){
    const nodes={
      'Build Fetch Candidates':[],
      'Build Fetch Candidates Retry 1':[],
      'Build Fetch Candidates Retry 2':[],
      'Fetch Source Page':[fetch],
    };
    nodes[activeNode]=[candidate];

    const out=runCode('Normalize Evidence',{
      nodes,
      json:extracted,
      itemIndex:0,
    }).json;

    assert.equal(out.research_run_id,candidate.research_run_id,activeNode);
    assert.equal(out.canonical_url,candidate.canonical_url,activeNode);
    assert.equal(out.source_http_status,200,activeNode);
    assert.match(out.content_text,/LiDAR mierzy czas/,activeNode);
  }
});

test('M4 evidence normalization no longer depends on .item pairing from a specific candidate builder',()=>{
  const code=byName['Normalize Evidence'].parameters.jsCode;
  assert.doesNotMatch(code,/Build Fetch Candidates'\)\.item/u);
  assert.doesNotMatch(code,/Fetch Source Page'\)\.item/u);
  assert.match(code,/Build Fetch Candidates Retry 2/u);
  assert.match(code,/Build Fetch Candidates Retry 1/u);
  assert.match(code,/\$itemIndex/u);
});
