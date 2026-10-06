/* Dependent category pickers shared by Diagnosis and My Garage. */
(() => {
  const form = document.getElementById('garageForm');
  const category = document.getElementById('garageCategory');
  const year = document.getElementById('garageYear');
  const ids = ['garageMake', 'garageModel', 'garageEngine'];
  const fields = ['makes', 'models', 'engines'];
  const names = ['make', 'model', 'engine / transmission'];
  const manual = '__manual__';
  const retry = '__retry__';
  const inputs = ids.map(id => document.getElementById(id));
  const generations = [0, 0, 0];
  const requests = new Map();
  const cache = new Map();
  const selects = inputs.map((input, i) => {
    const select = document.createElement('select');
    select.id = input.id + 'Picker';
    select.setAttribute('aria-label', 'Choose ' + names[i]);
    input.before(select);
    input.setAttribute('aria-label', 'Enter ' + names[i] + ' manually');
    return select;
  });
  const help = document.createElement('p');
  help.className = 'muted wide';
  help.setAttribute('role', 'status');
  document.getElementById('itemFields').appendChild(help);
  const automotive = () => category.value === 'automotive';
  // Starter model families, not a complete or year-specific parts catalog.
  const catalogs = {
    motorcycle: {
      Honda:[],Yamaha:[],Kawasaki:[],Suzuki:[],'Harley-Davidson':[],BMW:[],Ducati:[],KTM:[],Triumph:[],Indian:[],Aprilia:[],'Royal Enfield':[]
    },
    appliance: {
      GE:['GFW550SSNWW','GDT645SYNFS'],Samsung:['DVE50R5400V','WF45R6100AW'],
      Whirlpool:['WED4815EW','WTW5000DW'],Maytag:['MER6600FZ','MEDC465HW'],
      Frigidaire:['FGF316DSA','FFCD2413US'],Electrolux:['ELFE7637AT','ELFW7637AT'],
      LG:['DLE3400W','WM4000HWA'],Bosch:['SHEM63W55N'],
      Amana:['NTW4516FW','NED4655EW'],KitchenAid:['KDTM404KPS'],
      Kenmore:[],Hotpoint:[],Haier:[],Miele:[],Hisense:[],Beko:[],Insignia:[],Danby:[]
    },
    equipment: {
      Ford:[],Kubota:[],'Massey Ferguson':[],'New Holland':[],'Case IH':[],'International Harvester':[],'Allis-Chalmers':[],Kioti:[],Mahindra:[],
      Yamaha:['G29 / Drive','Drive2'], 'Club Car':['DS','Precedent','Onward'], 'E-Z-GO':['TXT','RXV'],
      Honda:['GX160','GX200','GX390'], 'Briggs & Stratton':['Intek','Vanguard'],
      Kohler:['Command','Courage'], 'John Deere':['D100','D130','E100','S100'],
      Husqvarna:['YTH18542','Z254'],Toro:['TimeCutter','Recycler'],
      'Cub Cadet':['XT1','ZT1'],Craftsman:[],STIHL:[],Echo:[],Ryobi:[],Generac:[],DeWalt:[],Makita:[],Milwaukee:[],Greenworks:[]
    },
    home: {
      Carrier:['Infinity','Performance','Comfort'],Trane:['XR14','XR16','XV20i'],Lennox:['Merit','Elite','Signature'],Goodman:['GSX14','GSX16'],Rheem:['Classic','Prestige'],Ruud:['Achiever','Ultra'],York:['Affinity','LX'],Amana:[],
      'American Standard':[], 'A. O. Smith':[], 'Bradford White':[],Rinnai:[],Navien:[],
      Honeywell:['T6 Pro','T9','T10 Pro'],Nest:['Learning Thermostat','Thermostat E'],Ecobee:['SmartThermostat','Smart Thermostat Premium'],LiftMaster:['8500','87504'],Chamberlain:['B2405','B6753T'],Genie:['StealthDrive','SilentMax']
    }
  };
  const farmMakes = ['John Deere','Ford','Kubota','Massey Ferguson','New Holland','Case IH','International Harvester','Allis-Chalmers','Kioti','Mahindra'];
  const yearModels = () => category.value === 'motorcycle' || (category.value === 'equipment' && farmMakes.includes(inputs[0].value));
  const supported = () => automotive() || !!catalogs[category.value];
  const dropdown = i => supported() && (automotive() || i < 2);
  const label = i => i === 0 && !['automotive','motorcycle','equipment'].includes(category.value) ? 'brand' : names[i];
  function setOptions(i, values = [], message = 'Choose ' + label(i), failed = false) {
    selects[i].replaceChildren(new Option(message, ''),
      ...values.map(value => new Option(value, value)),
      ...(failed ? [new Option('Try loading again', retry)] : []),
      new Option('Not listed? Enter manually', manual));
    selects[i].disabled = false;
  }
  function clearFrom(start) {
    for (let i = start; i < 3; i++) {
      generations[i]++;
      inputs[i].value = '';
      inputs[i].hidden = dropdown(i);
      setOptions(i, [], i === 0 ? (automotive() ? 'Choose a year first' : 'Choose ' + label(i)) : 'Choose ' + label(i - 1) + ' first');
    }
  }
  async function load(i) {
    if (!supported() || !dropdown(i)) return;
    if (!automotive() && !(yearModels() && i === 1)) {
      const catalog = catalogs[category.value];
      const options = i === 0 ? Object.keys(catalog).sort() : (catalog[inputs[0].value.trim()] || []);
      setOptions(i, options, options.length ? 'Choose ' + label(i) : 'No starter models listed');
      help.textContent = (category.value === 'motorcycle' || category.value === 'equipment' ? 'Choose a year and make to load matching motorcycle or farm tractor models. Unlisted items can be entered manually.' : 'Starter brand and model list. Confirm the exact model on the label; enter any unlisted model manually.');
      return;
    }
    const y = Number(year.value);
    if (!Number.isInteger(y) || y < 1900 || y > 2100 || !year.value) {setOptions(i, [], 'Choose a year first');return;}
    if (i > 0 && !inputs[0].value.trim()) return;
    if (i > 1 && !inputs[1].value.trim()) return;
    const generation = ++generations[i];
    setOptions(i, [], 'Loading ' + names[i] + ' choices…');
    const params = new URLSearchParams({year: year.value, category:category.value});
    if (i > 0) params.set('make', inputs[0].value.trim());
    if (i > 1) params.set('model', inputs[1].value.trim());
    try {
      const key = '/api/vehicles/' + fields[i] + '?' + params;
      let data = cache.get(key);
      if (!data) {
        // Reuse identical lookups; obsolete responses can never replace current choices.
        let pending = requests.get(key);
        if (!pending) {
          pending = (async () => {
            const response = await fetch(key, {signal: AbortSignal.timeout(10000)});
            if (!response.ok) throw new Error('catalog unavailable');
            const result = await response.json();
            if (!Array.isArray(result.options)) throw new Error('invalid catalog response');
            // Empty coverage is not cached: a newly added model must be discoverable.
            if (result.options.length) { if (cache.size >= 100) cache.delete(cache.keys().next().value); cache.set(key, result); }
            return result;
          })().finally(() => requests.delete(key));
          requests.set(key, pending);
        }
        data = await pending;
      }
      if (generation !== generations[i] || !supported()) return;
      setOptions(i, data.options, data.options.length ? 'Choose ' + label(i) : 'No verified models listed yet');
      help.textContent = data.options.length
        ? (yearModels() ? 'Models for ' + year.value + ' ' + inputs[0].value + ' from ' + data.source + '. Catalog coverage may be incomplete; enter an unlisted model manually.' : 'Choose your year, make, model, then engine / transmission. Not listed? Use manual entry.')
        : 'Catalog coverage is incomplete for this year and make. Use “Not listed? Enter manually.”';
    } catch {
      if (generation !== generations[i] || !supported()) return;
      setOptions(i, [], 'Could not load choices', true);
      help.textContent = 'The vehicle catalog could not load. Choose “Try loading again” to retry, or enter the details manually.';
    }
  }
  selects.forEach((select, i) => select.addEventListener('change', () => {
    if (select.value === retry) {
      inputs[i].value = '';
      clearFrom(i + 1);
      load(i);
      return;
    }
    generations[i]++;
    clearFrom(i + 1);
    inputs[i].value = select.value === manual ? '' : select.value;
    inputs[i].hidden = select.value !== manual;
    if(category.value==='appliance' && i===1 && !inputs[2].value){
      const types={GFW550SSNWW:'Washer',GDT645SYNFS:'Dishwasher',DVE50R5400V:'Dryer',WF45R6100AW:'Washer',WED4815EW:'Dryer',WTW5000DW:'Washer',MER6600FZ:'Range',MEDC465HW:'Dryer',FGF316DSA:'Range',FFCD2413US:'Dishwasher',ELFE7637AT:'Dryer',ELFW7637AT:'Washer',DLE3400W:'Dryer',WM4000HWA:'Washer',SHEM63W55N:'Dishwasher',NTW4516FW:'Washer',NED4655EW:'Dryer',KDTM404KPS:'Dishwasher'};
      inputs[2].value=types[select.value]||'';
    }
    if (select.value === manual) inputs[i].focus();
    else if (i < 2) load(i + 1);
  }));
  inputs.forEach((input, i) => input.addEventListener('input', () => clearFrom(i + 1)));
  inputs.forEach((input, i) => input.addEventListener('change', () => {
    if (i < 2) load(i + 1);
  }));
  let timer;
  year.addEventListener('input', () => {
    if (!supported()) return;
    clearTimeout(timer);
    if(!automotive()){clearFrom(1);timer=setTimeout(()=>load(1),300);}
    else {clearFrom(0);timer=setTimeout(()=>load(0),300);}
  });
  function configure() {
    clearTimeout(timer);
    clearFrom(0);
    selects.forEach((select,i) => {select.hidden = !dropdown(i);select.setAttribute('aria-label','Choose ' + label(i));inputs[i].setAttribute('aria-label','Enter ' + label(i) + ' manually');});
    inputs.forEach((input,i) => input.hidden = dropdown(i));
    help.hidden = !supported();
    help.textContent = 'Choose a year to load vehicle choices. Catalog covers EPA-listed cars and light trucks; other vehicles can be entered manually.';
    if (supported()) load(0);
  }
  category.addEventListener('change', configure);
  form.addEventListener('pocket:item-reset', configure);
  form.addEventListener('pocket:item-loaded', () => {
    clearTimeout(timer);
    for(let i=0;i<3;i++){
      generations[i]++;
      const value=inputs[i].value;
      setOptions(i,value?[value]:[]);
      selects[i].value=value;
      selects[i].hidden=!dropdown(i);
      inputs[i].hidden=dropdown(i);
    }
    help.hidden=!supported();
    if(yearModels() && year.value && inputs[0].value){
      const savedModel=inputs[1].value;
      load(1).then(()=>{if(savedModel && inputs[1].value===savedModel){
        if(![...selects[1].options].some(option=>option.value===savedModel)) selects[1].add(new Option(savedModel + ' (saved; confirm model)',savedModel));
        selects[1].value=savedModel;
      }});
    }
  });
  // reset fires before reset values are applied and category is restored by app.js.
  form.addEventListener('reset', () => {
    clearFrom(0);
    queueMicrotask(configure);
  });
  configure();
})();
