// Elevate navbar with shadow once the page scrolls
const navbar = document.getElementById('navbar');
if (navbar) {
  const updateNavbarState = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 12);
  };
  updateNavbarState();
  window.addEventListener('scroll', updateNavbarState, { passive: true });
}

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('open');
    navToggle.classList.toggle('open');
  });
}

// Crop dropdown
const cropDropdown = document.getElementById('cropDropdown');
const cropDropdownToggle = document.getElementById('cropDropdownToggle');
const cropDropdownMenu = document.getElementById('cropDropdownMenu');

if (cropDropdownToggle && cropDropdownMenu) {
  cropDropdownToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = cropDropdownMenu.classList.toggle('open');
    cropDropdownToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  document.addEventListener('click', (e) => {
    if (cropDropdown && !cropDropdown.contains(e.target)) {
      cropDropdownMenu.classList.remove('open');
      cropDropdownToggle.setAttribute('aria-expanded', 'false');
    }
  });

  cropDropdownMenu.querySelectorAll('.dropdown-item.disabled').forEach((item) => {
    item.addEventListener('click', () => {
      const cropName = item.dataset.crop
        ? item.dataset.crop.charAt(0).toUpperCase() + item.dataset.crop.slice(1)
        : 'This crop';
      showToast(`${cropName} leaf disease detection is coming soon!`);
      cropDropdownMenu.classList.remove('open');
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
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );
  revealEls.forEach((el) => observer.observe(el));
} else {
  revealEls.forEach((el) => el.classList.add('in-view'));
}

// Image preview on upload page
const input = document.getElementById('leaf_image');
const preview = document.getElementById('preview');
const dropzoneText = document.getElementById('dropzone-text');
if (input && preview && dropzoneText) {
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (file) {
      preview.src = URL.createObjectURL(file);
      preview.style.display = 'block';
      dropzoneText.style.display = 'none';
    }
  });
}
