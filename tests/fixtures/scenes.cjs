// API contract fixtures, not claims about the current contents of Wikipedia.
// Surface forms model real source-article links; no topic aliases live in resolver code.
const entities = [
  ['Terrestrial planet', 'Q128207', ['Планети земної групи', 'Планеты земной группы', 'Planeta skalista', 'Terrestrial planet'], ['планетами земної групи', 'планетами земной группы', 'planetami skalistymi', 'terrestrial planets']],
  ['Gas giant', 'Q121750', ['Газові планети', 'Газовый гигант', 'Gazowy olbrzym', 'Gas giant'], ['газовими гігантами', 'газовыми гигантами', 'gazowymi olbrzymami', 'gas giants']],
  ['Small Solar System body', 'Q175070', ['Малі тіла Сонячної системи', 'Малое тело Солнечной системы', 'Małe ciało Układu Słonecznego', 'Small Solar System body'], ['малими тілами', 'малыми телами', 'małymi ciałami', 'small bodies']],
  ['Asteroid belt', 'Q3502', ['Пояс астероїдів', 'Пояс астероидов', 'Pas planetoid', 'Asteroid belt'], []],
  ['Trans-Neptunian object', 'Q6599', ["Транснептуновий об'єкт", 'Транснептуновый объект', 'Obiekt transneptunowy', 'Trans-Neptunian object'], ["транснептунові об'єкти", 'транснептуновые объекты', 'obiekty transneptunowe', 'trans-Neptunian objects']],
  ['Solar wind', 'Q79833', ['Сонячний вітер', 'Солнечный ветер', 'Wiatr słoneczny', 'Solar wind'], []],
  ['Mercury (planet)', 'Q308', ['Меркурій', 'Меркурий', 'Merkury', 'Mercury'], []],
  ['Earth', 'Q2', ['Земля', 'Земля', 'Ziemia', 'Earth'], []],
  ['Mars', 'Q111', ['Марс', 'Марс', 'Mars', 'Mars'], []],
  ['Jupiter', 'Q319', ['Юпітер', 'Юпитер', 'Jowisz', 'Jupiter'], []],
  ['Neptune', 'Q332', ['Нептун', 'Нептун', 'Neptun', 'Neptune'], []],
  ['Pluto', 'Q339', ['Плутон', 'Плутон', 'Pluton', 'Pluto'], []],
  ['Solar System', 'Q544', ['Сонячна система', 'Солнечная система', 'Układ Słoneczny', 'Solar System'], []],
  ['Solar corona', 'Q60186', ['Сонячна корона', 'Солнечная корона', 'Korona słoneczna', 'Solar corona'], []],
  ['Venus', 'Q313', ['Венера', 'Венера', 'Wenus', 'Venus'], []],
  ['Saturn', 'Q193', ['Сатурн', 'Сатурн', 'Saturn', 'Saturn'], []],
  ['Uranus', 'Q324', ['Уран', 'Уран', 'Uran', 'Uranus'], []],
];
const texts = {
  uk: [
    'Меркурій, Венера, Земля та Марс, звані також планетами земної групи, складаються з силікатів.',
    'Юпітер, Сатурн, Уран та Нептун, звані також газовими гігантами, масивніші, ніж планети земної групи.',
    'У Сонячній системі є дві ділянки, заповнені малими тілами.',
    'Пояс астероїдів, що розташований між Марсом і Юпітером, подібний до планет земної групи.',
    "Найбільшими об'єктами поясу астероїдів є Церера, Паллада та Веста.",
    "За орбітою Нептуна розташовано транснептунові об'єкти, що містять замерзлу воду.",
    'Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида.',
    'Сонячний вітер, потік плазми від Сонця, утворює бульбашку, яка називається геліосферою.',
  ],
  ru: [
    'Меркурий, Венера, Земля и Марс, называемые также планетами земной группы, состоят из силикатов.',
    'Юпитер, Сатурн, Уран и Нептун, называемые также газовыми гигантами, массивнее, чем планеты земной группы.',
    'В Солнечной системе есть две области, заполненные малыми телами.',
    'Пояс астероидов, который расположен между Марсом и Юпитером, похож на планеты земной группы.',
    'Крупнейшими объектами пояса астероидов являются Церера, Паллада и Веста.',
    'За орбитой Нептуна расположены транснептуновые объекты, которые содержат лёд.',
    'Крупнейшими из них являются Плутон, Седна, Хаумеа, Макемаке и Эрида.',
    'Солнечный ветер, поток плазмы от Солнца, образует пузырь, который называется гелиосферой.',
  ],
  pl: [
    'Merkury, Wenus, Ziemia i Mars, zwane także planetami skalistymi, składają się z krzemianów.',
    'Jowisz, Saturn, Uran i Neptun, zwane także gazowymi olbrzymami, są masywniejsze niż planety skaliste.',
    'W Układzie Słonecznym są dwa obszary wypełnione małymi ciałami.',
    'Pas planetoid, który znajduje się między Marsem i Jowiszem, przypomina planety skaliste.',
    'Największymi obiektami pasa planetoid są Ceres, Pallas i Westa.',
    'Za orbitą Neptuna znajdują się obiekty transneptunowe, które zawierają lód.',
    'Największymi z nich są Pluton, Sedna, Haumea, Makemake i Eris.',
    'Wiatr słoneczny, strumień plazmy ze Słońca, tworzy bańkę zwaną heliosferą.',
  ],
  en: [
    'Mercury, Venus, Earth and Mars, also called terrestrial planets, consist of silicates.',
    'Jupiter, Saturn, Uranus and Neptune, also known as gas giants, are more massive than terrestrial planets.',
    'In the Solar System there are two regions filled with small bodies.',
    'The asteroid belt, which lies between Mars and Jupiter, resembles terrestrial planets.',
    'The largest objects of the asteroid belt are Ceres, Pallas and Vesta.',
    'Beyond the orbit of Neptune lie trans-Neptunian objects, which contain ice.',
    'The largest of them are Pluto, Sedna, Haumea, Makemake and Eris.',
    'Solar wind, a stream of plasma from the Sun, forms a bubble called the heliosphere.',
  ],
};
const expected = [0, 1, 2, 3, 3, 4, 4, 5].map(i => entities[i][0]);
const langs = ['uk', 'ru', 'pl', 'en'];
function source(lang) {
  const i = langs.indexOf(lang);
  return entities.map(e => `[[${e[2][i]}]] ${e[3][i] ? `[[${e[2][i]}|${e[3][i]}]]` : ''}`).join('\n');
}
function scenes(lang) {
  return texts[lang].map(text => ({text, searchTerms: [`visualsource::${lang}::${encodeURIComponent(entities[12][2][langs.indexOf(lang)])}::Solar%20System`]}));
}
module.exports = {entities, texts, expected, langs, source, scenes};
