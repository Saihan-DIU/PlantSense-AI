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

  form.addEventListener('submit', (e) => {
    const error = validate(input.files[0]);
    if (error) {
      e.preventDefault();
      setError(error);
      return;
    }
    submitBtn.classList.add('is-loading');
    submitBtn.querySelector('.btn__label').textContent = 'Analyzing…';
  });

  // Reset the button if the user navigates back to this page from the result
  window.addEventListener('pageshow', () => {
    submitBtn.classList.remove('is-loading');
    submitBtn.querySelector('.btn__label').textContent = 'Analyze leaf';
  });
}
