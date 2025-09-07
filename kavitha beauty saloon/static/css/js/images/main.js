// Smooth scroll for navigation links
document.querySelectorAll('nav ul li a').forEach(link => {
  link.addEventListener('click', function(e) {
    const href = this.getAttribute('href');
    if (href.startsWith('#')) {
      e.preventDefault();
      document.querySelector(href).scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Booking form validation
const bookingForm = document.querySelector('.booking-form');
if (bookingForm) {
  bookingForm.addEventListener('submit', function(e) {
    let valid = true;
    const name = bookingForm.querySelector('#name');
    const email = bookingForm.querySelector('#email');
    const phone = bookingForm.querySelector('#phone');
    const date = bookingForm.querySelector('#date');
    const time = bookingForm.querySelector('#time');
    if (!name.value.trim()) valid = false;
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)) valid = false;
    if (!/^\d{10}$/.test(phone.value.replace(/\D/g, ''))) valid = false;
    if (!date.value) valid = false;
    if (!time.value) valid = false;
    if (!valid) {
      e.preventDefault();
      alert('Please fill out all fields correctly.');
    }
  });
}

// Contact form validation
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', function(e) {
    let valid = true;
    const name = contactForm.querySelector('#name');
    const email = contactForm.querySelector('#email');
    const message = contactForm.querySelector('#message');
    if (!name.value.trim()) valid = false;
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)) valid = false;
    if (!message.value.trim()) valid = false;
    if (!valid) {
      e.preventDefault();
      alert('Please fill out all fields correctly.');
    }
  });
}

// Highlight active nav link
const navLinks = document.querySelectorAll('nav ul li a');
const currentPath = window.location.pathname;
navLinks.forEach(link => {
  if (link.getAttribute('href') === currentPath) {
    link.classList.add('active');
  }
});