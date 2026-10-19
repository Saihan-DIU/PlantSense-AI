// Interface text for the page language (embedded by base.html from i18n.py)
const LANG = document.documentElement.lang || 'en';
const I18N = (() => {
  try { return JSON.parse(document.getElementById('i18n').textContent); } catch { return {}; }
})();
function tr(key, vars = {}) {
  let text = I18N[key] || key;
  for (const [name, value] of Object.entries(vars)) text = text.split(`{${name}}`).join(value);
  return text;
}
// Bangla pages show Bangla digits
const digits = (value) => (LANG === 'bn' ? String(value).replace(/[0-9]/g, (d) => '০১২৩৪৫৬৭৮৯'[d]) : String(value));

// Remember the language the visitor picked (base.html uses it on their next visit)
document.querySelectorAll('.lang-switch [data-lang]').forEach((link) => {
  link.addEventListener('click', () => {
    try { localStorage.setItem('plantsense-lang', link.dataset.lang); } catch { /* storage blocked */ }
  });
});

// Navbar border once the page scrolls
const navbar = document.getElementById('navbar');
if (navbar) {
  const updateNavbarState = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 8);
  };
  updateNavbarState();
  window.addEventListener('scroll', updateNavbarState, { passive: true });
}

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
if (navToggle && navMenu) {
  const setNavOpen = (open) => {
    navMenu.classList.toggle('open', open);
    navToggle.classList.toggle('open', open);
    navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    navToggle.setAttribute('aria-label', open ? tr('nav.close_menu') : tr('nav.open_menu'));
  };
  navToggle.addEventListener('click', () => setNavOpen(!navMenu.classList.contains('open')));
  // Close the mobile menu after following an in-page link
  navMenu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setNavOpen(false));
  });
}

// Crop dropdown
const cropDropdown = document.getElementById('cropDropdown');
const cropDropdownToggle = document.getElementById('cropDropdownToggle');
const cropDropdownMenu = document.getElementById('cropDropdownMenu');

if (cropDropdownToggle && cropDropdownMenu) {
  const setDropdownOpen = (open) => {
    cropDropdownMenu.classList.toggle('open', open);
    cropDropdownToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  };

  cropDropdownToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    setDropdownOpen(!cropDropdownMenu.classList.contains('open'));
  });

  document.addEventListener('click', (e) => {
    if (cropDropdown && !cropDropdown.contains(e.target)) setDropdownOpen(false);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && cropDropdownMenu.classList.contains('open')) {
      setDropdownOpen(false);
      cropDropdownToggle.focus();
    }
  });

  cropDropdownMenu.querySelectorAll('.dropdown-item.disabled').forEach((item) => {
    item.addEventListener('click', () => {
      const crop = item.dataset.crop || 'tomato';
      showToast(tr('js.coming_soon', { crop: tr(`crop.${crop.charAt(0).toUpperCase()}${crop.slice(1)}`) }));
      setDropdownOpen(false);
    });
  });
}

// Toast helper
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => toast.classList.remove('show'), 3000);
}

// Scroll-reveal animation for cards/sections
const revealEls = document.querySelectorAll('.reveal');
if (revealEls.length && 'IntersectionObserver' in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );
  revealEls.forEach((el) => observer.observe(el));
} else {
  revealEls.forEach((el) => el.classList.add('in-view'));
}

// Upload: preview, drag & drop, format conversion, validation, loading state
const form = document.getElementById('upload-form');
const input = document.getElementById('leaf_image');
const dropzone = document.getElementById('dropzone');
const dropzoneText = document.getElementById('dropzone-text');
const dropzonePreview = document.getElementById('dropzone-preview');
const preview = document.getElementById('preview');
const fileName = document.getElementById('file-name');
const uploadError = document.getElementById('upload-error');
const submitBtn = document.getElementById('submit-btn');

if (form && input && dropzone) {
  form.noValidate = true; // show our inline message instead of the browser tooltip
  // Server uploads are capped by MAX_CONTENT_LENGTH in app.py; in-browser analysis uploads nothing.
  const maxMb = Number(form.dataset.maxMb) || 8;
  const formatSize = (bytes) =>
    digits(bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`);

  // HEIC/TIFF converters live in a separate module, loaded on first use
  let formatsModule = null;
  const formats = () => (formatsModule ||= import('/static/js/image-formats.js'));

  const setError = (message) => {
    uploadError.textContent = message || '';
    uploadError.hidden = !message;
  };

  const setLoading = (loading, label) => {
    submitBtn.classList.toggle('is-loading', loading);
    submitBtn.querySelector('.btn__label').textContent = label || tr('upload.analyze');
  };

  let selected = null; // the photo to analyze (converted to PNG if needed)
  let pending = null;  // in-flight conversion
  let token = 0;       // ignores results for photos the user has since replaced

  const clearPreview = () => {
    if (preview.src.startsWith('blob:')) URL.revokeObjectURL(preview.src);
    preview.removeAttribute('src');
    fileName.textContent = '';
    dropzone.classList.remove('has-file');
    dropzoneText.hidden = false;
    dropzonePreview.hidden = true;
  };

  const showPreview = (file, label) => {
    if (preview.src.startsWith('blob:')) URL.revokeObjectURL(preview.src);
    if (file) preview.src = URL.createObjectURL(file);
    else preview.removeAttribute('src');
    fileName.textContent = label;
    dropzone.classList.add('has-file');
    dropzoneText.hidden = true;
    dropzonePreview.hidden = false;
  };

  const handleFile = async (file) => {
    const mine = ++token;
    selected = null;
    pending = null;
    setError('');
    if (!file) { clearPreview(); return; }
    if (file.size > maxMb * 1024 * 1024) {
      setError(tr('js.too_big', { size: formatSize(file.size), max: digits(maxMb) }));
      input.value = '';
      clearPreview();
      return;
    }
    const label = `${file.name} · ${formatSize(file.size)}`;
    showPreview(null, `${label} · ${tr('js.preparing')}`);
    pending = formats().then((m) => m.normalizeImage(file, { forServer: !browser }));
    try {
      const ready = await pending;
      if (mine !== token) return;
      if (!browser && ready.size > maxMb * 1024 * 1024) {
        throw new Error(tr('js.too_big_converted', { size: formatSize(ready.size), max: digits(maxMb) }));
      }
      selected = ready;
      showPreview(ready, label);
      // Server mode posts the form, so send the converted image instead of the original
      if (!browser && ready !== file) {
        const dt = new DataTransfer();
        dt.items.add(ready);
        input.files = dt.files;
      }
    } catch (err) {
      if (mine !== token) return;
      // image-formats.js errors carry a message key
      setError(err.key ? tr(err.key) : tr('js.unreadable'));
      input.value = '';
      clearPreview();
    } finally {
      if (mine === token) pending = null;
    }
  };

  input.addEventListener('change', () => {
    // Ignore the change event fired when we swap in a converted file ourselves
    if (selected && input.files[0] === selected) return;
    handleFile(input.files[0]);
  });

  ['dragenter', 'dragover'].forEach((type) =>
    dropzone.addEventListener(type, (e) => {
      e.preventDefault();
      dropzone.classList.add('is-dragover');
    })
  );
  ['dragleave', 'drop'].forEach((type) =>
    dropzone.addEventListener(type, (e) => {
      e.preventDefault();
      dropzone.classList.remove('is-dragover');
    })
  );
  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer && e.dataTransfer.files;
    if (!files || !files.length) return;
    input.files = files;
    handleFile(files[0]);
  });

  // Clear the selected photo so the next analysis starts from an empty dropzone
  const resetUpload = () => {
    token++;
    selected = null;
    pending = null;
    form.reset();
    clearPreview();
    setError('');
  };

  const browserConfig = document.getElementById('crop-config');
  const browser = form.dataset.mode === 'browser' && browserConfig
    ? setupBrowserInference(JSON.parse(browserConfig.textContent), { setError, setLoading, resetUpload })
    : null;

  input.addEventListener('change', () => { if (input.files[0]) browser?.warmUp(); });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (pending) {
      setLoading(true, tr('js.preparing_photo'));
      try { await pending; } catch { /* error already shown */ }
      setLoading(false);
    }
    if (!selected) {
      if (!uploadError.textContent) setError(tr('js.choose_photo'));
      return;
    }
    if (browser) {
      browser.analyze(selected);
      return;
    }
    setLoading(true, tr('js.analyzing'));
    form.submit();
  });

  // Reset the button if the user navigates back to this page from the result
  window.addEventListener('pageshow', () => setLoading(false));
}

// Static build: run the model in the browser and render the result in-page.
function setupBrowserInference(config, { setError, setLoading, resetUpload }) {
  const landing = document.getElementById('landing');
  const resultView = document.getElementById('result-view');
  const status = document.getElementById('model-status');
  const statusText = document.getElementById('model-status-text');
  const statusPct = document.getElementById('model-status-pct');
  const statusFill = document.getElementById('model-status-fill');
  const $ = (id) => document.getElementById(id);

  let predictorPromise = null;
  let downloaded = 0;
  let waiting = false; // true while the user is waiting on a result

  const showStatus = (text, fraction) => {
    status.hidden = false;
    statusText.textContent = text;
    const known = typeof fraction === 'number';
    status.classList.toggle('is-indeterminate', !known);
    statusPct.textContent = known ? `${digits(Math.round(fraction * 100))}%` : '';
    statusFill.style.width = known ? `${fraction * 100}%` : '';
  };
  const hideStatus = () => { status.hidden = true; };

  const onDownload = (fraction) => {
    downloaded = fraction;
    if (waiting && fraction < 1) {
      showStatus(tr('js.downloading', { mb: digits(config.model_size_mb) }), fraction);
    }
  };

  const getPredictor = () => {
    if (!predictorPromise) {
      predictorPromise = import(config.inference_module).then((m) => m.createPredictor(config));
      predictorPromise.catch(() => { predictorPromise = null; });
    }
    return predictorPromise;
  };

  const warmUp = () => getPredictor().then((p) => p.preload(onDownload)).catch(() => {});

  // Start downloading right away unless the visitor is on a slow or metered connection.
  const conn = navigator.connection;
  const slow = conn && (conn.saveData || /2g|3g/.test(conn.effectiveType || ''));
  if (!slow) {
    const start = () => warmUp();
    if ('requestIdleCallback' in window) requestIdleCallback(start, { timeout: 3000 });
    else setTimeout(start, 1500);
  }

  const round2 = (n) => Math.round(n * 100) / 100;
  // Class names in the page language (from i18n.localized_info)
  const pretty = (name) => (config.info[name] && config.info[name].name) || name.replace(/_/g, ' ');

  const render = (result, file) => {
    const info = config.info[result.className] || {};
    const healthy = Boolean(info.is_healthy);
    const tone = healthy ? 'healthy' : 'disease';
    const confidence = round2(result.confidence);

    const img = $('result-image');
    if (img.src.startsWith('blob:')) URL.revokeObjectURL(img.src);
    img.src = URL.createObjectURL(file);

    $('result-verdict').className = `card verdict verdict--${tone}`;
    $('result-status').className = `status status--${tone}`;
    $('result-status-text').textContent = healthy ? tr('result.healthy') : tr('result.disease');
    $('result-title').textContent = pretty(result.className);
    $('result-desc').textContent = info.description || '';
    $('result-desc').hidden = !info.description;

    const gauge = $('result-gauge');
    gauge.style.setProperty('--p', confidence);
    gauge.setAttribute('aria-label', tr('result.confidence_aria', { value: digits(confidence) }));
    $('result-gauge-value').textContent = digits(Math.round(confidence));
    $('result-lowconf').hidden = confidence >= 60;

    const steps = info.instructions || [];
    $('result-actions-card').hidden = !steps.length;
    $('result-actions-title').textContent = healthy ? tr('result.care') : tr('result.actions');
    $('result-actions-list').replaceChildren(...steps.map((step) => {
      const li = document.createElement('li');
      li.textContent = step;
      return li;
    }));

    const list = $('result-prob-list');
    const template = list.firstElementChild;
    list.replaceChildren(...result.ranked.map(([name, prob], i) => {
      const li = template.cloneNode(true);
      li.className = i === 0 ? 'prob prob--top' : 'prob';
      li.querySelector('.prob__row span').textContent = pretty(name);
      li.querySelector('.prob__row strong').textContent = `${digits(round2(prob))}%`;
      li.querySelector('.prob__fill').style.width = `${round2(prob)}%`;
      return li;
    }));

    document.title = tr('title.result', { label: pretty(result.className), Crop: config.crop_label });
  };

  const pageTitle = document.title;
  const showResult = () => {
    landing.hidden = true;
    resultView.hidden = false;
    window.scrollTo({ top: 0 });
  };
  const showLanding = () => {
    resultView.hidden = true;
    landing.hidden = false;
    document.title = pageTitle;
    resetUpload();
  };

  // Browser back button returns from the result to the upload page.
  window.addEventListener('popstate', () => {
    if (!resultView.hidden) {
      showLanding();
      document.getElementById('upload')?.scrollIntoView();
    }
  });
  resultView.querySelectorAll('[data-action="new-analysis"]').forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      if (history.state && history.state.view === 'result') history.back();
      else { showLanding(); document.getElementById('upload')?.scrollIntoView(); }
    });
  });

  const analyze = async (file) => {
    setError('');
    setLoading(true, tr('js.analyzing'));
    waiting = true;
    if (downloaded < 1) onDownload(downloaded);
    try {
      const predictor = await getPredictor();
      const result = await predictor.predict(file, {
        onDownload,
        onStage: () => showStatus(tr('js.analyzing_leaf')),
      });
      render(result, file);
      history.pushState({ view: 'result' }, '', '#result');
      showResult();
    } catch (err) {
      console.error(err);
      setError(
        navigator.onLine === false
          ? tr('js.offline')
          : tr('js.failed')
      );
    } finally {
      waiting = false;
      hideStatus();
      setLoading(false);
    }
  };

  // A reload on #result has no result to show; start from the upload page.
  if (location.hash === '#result') history.replaceState(null, '', location.pathname);

  return { warmUp, analyze };
}
