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
    navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
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
      const cropName = item.dataset.crop
        ? item.dataset.crop.charAt(0).toUpperCase() + item.dataset.crop.slice(1)
        : 'This crop';
      showToast(`${cropName} leaf disease detection is coming soon.`);
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

// Upload: preview, drag & drop, client-side validation, loading state
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024; // keep in sync with MAX_CONTENT_LENGTH in app.py
const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp'];

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
  const formatSize = (bytes) =>
    bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;

  const setError = (message) => {
    uploadError.textContent = message || '';
    uploadError.hidden = !message;
  };

  const validate = (file) => {
    if (!file) return 'Please choose a leaf photo first.';
    if (!ACCEPTED_TYPES.includes(file.type)) return 'Unsupported file type. Please upload a PNG, JPG or WEBP image.';
    if (file.size > MAX_UPLOAD_BYTES) return `That file is ${formatSize(file.size)}. The limit is 8 MB.`;
    return '';
  };

  const showFile = (file) => {
    const error = validate(file);
    setError(error);
    if (error || !file) {
      input.value = '';
      dropzone.classList.remove('has-file');
      dropzoneText.hidden = false;
      dropzonePreview.hidden = true;
      return;
    }
    if (preview.src.startsWith('blob:')) URL.revokeObjectURL(preview.src);
    preview.src = URL.createObjectURL(file);
    fileName.textContent = `${file.name} · ${formatSize(file.size)}`;
    dropzone.classList.add('has-file');
    dropzoneText.hidden = true;
    dropzonePreview.hidden = false;
  };

  input.addEventListener('change', () => showFile(input.files[0]));

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
    showFile(files[0]);
  });

  const setLoading = (loading, label) => {
    submitBtn.classList.toggle('is-loading', loading);
    submitBtn.querySelector('.btn__label').textContent = label || 'Analyze leaf';
  };

  // Clear the selected photo so the next analysis starts from an empty dropzone
  const resetUpload = () => {
    form.reset();
    if (preview.src.startsWith('blob:')) URL.revokeObjectURL(preview.src);
    preview.removeAttribute('src');
    fileName.textContent = '';
    dropzone.classList.remove('has-file');
    dropzoneText.hidden = false;
    dropzonePreview.hidden = true;
    setError('');
  };

  const browserConfig = document.getElementById('crop-config');
  const browser = form.dataset.mode === 'browser' && browserConfig
    ? setupBrowserInference(JSON.parse(browserConfig.textContent), { setError, setLoading, resetUpload })
    : null;

  input.addEventListener('change', () => { if (input.files[0]) browser?.warmUp(); });

  form.addEventListener('submit', (e) => {
    const file = input.files[0];
    const error = validate(file);
    if (error) {
      e.preventDefault();
      setError(error);
      return;
    }
    if (browser) {
      e.preventDefault();
      browser.analyze(file);
      return;
    }
    setLoading(true, 'Analyzing…');
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
    statusPct.textContent = known ? `${Math.round(fraction * 100)}%` : '';
    statusFill.style.width = known ? `${fraction * 100}%` : '';
  };
  const hideStatus = () => { status.hidden = true; };

  const onDownload = (fraction) => {
    downloaded = fraction;
    if (waiting && fraction < 1) {
      showStatus(`Downloading the AI model (one time, ${config.model_size_mb} MB)…`, fraction);
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
  const pretty = (name) => name.replace(/_/g, ' ');

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
    $('result-status-text').textContent = healthy ? 'Healthy leaf' : 'Disease detected';
    $('result-title').textContent = pretty(result.className);
    $('result-desc').textContent = info.description || '';
    $('result-desc').hidden = !info.description;

    const gauge = $('result-gauge');
    gauge.style.setProperty('--p', confidence);
    gauge.setAttribute('aria-label', `Confidence ${confidence} percent`);
    $('result-gauge-value').textContent = Math.round(confidence);
    $('result-lowconf').hidden = confidence >= 60;

    const steps = info.instructions || [];
    $('result-actions-card').hidden = !steps.length;
    $('result-actions-title').textContent = healthy ? 'Care recommendations' : 'Recommended actions';
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
      li.querySelector('.prob__row strong').textContent = `${round2(prob)}%`;
      li.querySelector('.prob__fill').style.width = `${round2(prob)}%`;
      return li;
    }));

    document.title = `${pretty(result.className)} — ${config.crop_label} Diagnosis · PlantSense AI`;
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
    setLoading(true, 'Analyzing…');
    waiting = true;
    if (downloaded < 1) onDownload(downloaded);
    try {
      const predictor = await getPredictor();
      const result = await predictor.predict(file, {
        onDownload,
        onStage: () => showStatus('Analyzing the leaf…'),
      });
      render(result, file);
      history.pushState({ view: 'result' }, '', '#result');
      showResult();
    } catch (err) {
      console.error(err);
      setError(
        navigator.onLine === false
          ? 'You appear to be offline. Connect to the internet once so the AI model can download.'
          : 'Something went wrong while analyzing the image. Please try again or use a different photo.'
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
