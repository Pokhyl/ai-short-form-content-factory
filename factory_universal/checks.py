import app

def check():
 assert app.tokens('Volcanoes cats dogs species series')==['volcano','cat','dog','species','series']
 parser=app.WikiHTML('en',paragraphs_only=True)
 parser.feed('<h2>History</h2><div>Fragment</div><p>A complete paragraph.</p><ul><li>A list fragment.</li></ul><table><tr><td>Table fragment.</td></tr></table>')
 assert parser.text()=='A complete paragraph.'
 assert app.sentences('Energia zapobiega tzw. letnim blackoutom. Kolejne zdanie.')==['Energia zapobiega tzw. letnim blackoutom.','Kolejne zdanie.']
 for shots,beats in [(6,2),(6,3),(12,5),(18,6),(24,8)]:
  layout=app.shot_beats(shots,beats)
  assert len(layout)==shots and sorted(layout)==layout
  assert all(layout.count(i)>=2 for i in range(beats))
 anchor={'title':'Volcano','text':'Volcanoes emit lava ash magma gas from the crust of Earth.'}
 film={'title':'Volcano (1997 film)','text':'A film about lava ash magma gas in the crust of Earth.'}
 assert app.relevant_sources([film,anchor],'Volcano','en')==[anchor]
 slot={'text':'Solar thermal conversion produces heat.','visual_title':'Solar thermal collector'}
 fossil={'alt':'Chimneys, thermal power station, energy','height':1000,'width':800}
 solar={'alt':'Solar panels for thermal heating on a house','height':1000,'width':800}
 assert app.photo_score(fossil,slot,'Solar energy')<0
 assert app.photo_score(solar,slot,'Solar energy')>=0
 assert app.unsupported_qualifier('The largest mud volcanoes are enormous.','Volcano',[{'title':'Volcano'}])
 assert not app.unsupported_qualifier('The largest mud volcanoes are enormous.','Volcano',[{'title':'Volcano'},{'title':'Mud volcano'}])
 contexts=[{'title':'Lunar eclipse','visual_title':'Lunar eclipse','text':'The Moon moves through the shadow of Earth.'},{'title':'August 2009 lunar eclipse','visual_title':'August 2009 lunar eclipse','text':'The Moon moves through the shadow of Earth.'}]
 assert app.visual_context_title({'text':'The Moon moves through the shadow of Earth.'},contexts,'en')=='Lunar eclipse'
 assert app.photo_score({'alt':'Total solar eclipse of the sun','height':1000,'width':800},{'text':'A lunar eclipse occurs when the Moon enters the shadow of Earth.','visual_title':'Eclipse'},'Lunar eclipse')<0
 assert app.photo_score({'alt':'Total lunar eclipse showing the red Moon','height':1000,'width':800},{'text':'A lunar eclipse occurs when the Moon enters the shadow of Earth.','visual_title':'Lunar eclipse'},'Lunar eclipse')>=0
 assert app.photo_score({'provider':'pixabay','alt':'solar eclipse, eclipse, sun, lunar, moon','height':1000,'width':800},{'text':'A lunar eclipse darkens the Moon.','visual_title':'Eclipse'},'Lunar eclipse')<0
 assert app.photo_score({'provider':'pixabay','alt':'lunar eclipse, fantasy, sci-fi','height':1000,'width':800},{'text':'A lunar eclipse darkens the Moon.','visual_title':'Lunar eclipse'},'Lunar eclipse')<0
 assert app.safe_id('../unrelated') is None
 print('PASS: plural normalization, paragraph extraction, complete abbreviations, five shot layouts, homonym exclusion, owned UUID validation')

if __name__=='__main__':check()
