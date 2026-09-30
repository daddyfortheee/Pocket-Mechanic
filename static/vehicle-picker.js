/* One dependent vehicle picker shared by Diagnosis and My Garage. */
(() => {
  const form = document.getElementById('garageForm');
  const category = document.getElementById('garageCategory');
  const year = document.getElementById('garageYear');
  const ids = ['garageMake', 'garageModel', 'garageEngine'];
  const fields = ['makes', 'models', 'engines'];
  const names = ['make', 'model', 'engine / transmission'];
  const manual = '__manual__';
  const inputs = ids.map(id => document.getElementById(id));
  const generations = [0, 0, 0];
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
  form.appendChild(help);
  const automotive = () => category.value === 'automotive';
  function setOptions(i, values = [], message = 'Choose ' + names[i]) {
    selects[i].replaceChildren(new Option(message, ''),
      ...values.map(value => new Option(value, value)),
      new Option('Not listed? Enter manually', manual));
    selects[i].disabled = false;
  }
  function clearFrom(start) {
    for (let i = start; i < 3; i++) {
      generations[i]++;
      inputs[i].value = '';
      inputs[i].hidden = automotive();
      setOptions(i, [], i === 0 ? 'Choose a year first' : 'Choose ' + names[i - 1] + ' first');
    }
  }
  async function load(i) {
    if (!automotive()) return;
    const y = Number(year.value);
    if (!Number.isInteger(y) || y < 1900 || y > 2100 || !year.value) return;
    if (i > 0 && !inputs[0].value.trim()) return;
    if (i > 1 && !inputs[1].value.trim()) return;
    const generation = ++generations[i];
    setOptions(i, [], 'Loading ' + names[i] + ' choices…');
    const params = new URLSearchParams({year: year.value});
    if (i > 0) params.set('make', inputs[0].value.trim());
    if (i > 1) params.set('model', inputs[1].value.trim());
    try {
      const response = await fetch('/api/vehicles/' + fields[i] + '?' + params,
        {signal: AbortSignal.timeout(15000)});
      if (!response.ok) throw new Error('catalog unavailable');
      const data = await response.json();
      if (generation !== generations[i] || !automotive()) return;
      setOptions(i, data.options, data.options.length ? 'Choose ' + names[i] : 'No catalog matches');
      help.textContent = data.options.length
        ? 'Choose your year, make, model, then engine / transmission. Not listed? Use manual entry.'
        : 'No catalog matches for these details. Use “Not listed? Enter manually.”';
    } catch {
      if (generation !== generations[i] || !automotive()) return;
      setOptions(i, [], 'Catalog unavailable — enter manually');
      help.textContent = 'The vehicle catalog could not load. You can still enter and save your vehicle manually.';
    }
  }
  selects.forEach((select, i) => select.addEventListener('change', () => {
    generations[i]++;
    clearFrom(i + 1);
    inputs[i].value = select.value === manual ? '' : select.value;
    inputs[i].hidden = select.value !== manual;
    if (select.value === manual) inputs[i].focus();
    else if (i < 2) load(i + 1);
  }));
  inputs.forEach((input, i) => input.addEventListener('input', () => clearFrom(i + 1)));
  inputs.forEach((input, i) => input.addEventListener('change', () => {
    if (i < 2) load(i + 1);
  }));
  let timer;
  year.addEventListener('input', () => {
    clearTimeout(timer);
    clearFrom(0);
    timer = setTimeout(() => load(0), 300);
  });
  function configure() {
    clearTimeout(timer);
    clearFrom(0);
    selects.forEach(select => select.hidden = !automotive());
    inputs.forEach(input => input.hidden = automotive());
    help.hidden = !automotive();
    help.textContent = 'Choose a year to load vehicle choices. Catalog covers EPA-listed cars and light trucks; other vehicles can be entered manually.';
    if (automotive()) load(0);
  }
  category.addEventListener('change', configure);
  // reset fires before reset values are applied and category is restored by app.js.
  form.addEventListener('reset', () => {
    clearFrom(0);
    queueMicrotask(configure);
  });
  configure();
})();
