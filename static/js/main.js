document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile nav toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navbar = document.querySelector('.navbar');
    if (mobileToggle && navbar) {
        mobileToggle.addEventListener('click', () => {
            navbar.classList.toggle('mobile-active');
            // Toggle icon
            const icon = mobileToggle.querySelector('i');
            if (navbar.classList.contains('mobile-active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    // 2. Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar?.classList.add('scrolled');
        } else {
            navbar?.classList.remove('scrolled');
        }
    });

    // 3. Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.flash-toast');
    flashMessages.forEach(toast => {
        // Auto dismiss after 5s
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 500); // Wait for animation
        }, 5000);

        // Manual dismiss
        const closeBtn = toast.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 500);
            });
        }
    });

    // 4. Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 5. Number counter animation
    const counters = document.querySelectorAll('.kpi-value[data-value]');
    const animateCounters = () => {
        counters.forEach(counter => {
            const target = +counter.getAttribute('data-value');
            const duration = 1500; // ms
            const stepTime = Math.abs(Math.floor(duration / target));
            let current = 0;

            const increment = target / (duration / 16); // 60fps

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    counter.innerText = target.toLocaleString();
                    clearInterval(timer);
                } else {
                    counter.innerText = Math.ceil(current).toLocaleString();
                }
            }, 16);
        });
    };
    // Run counter animation (you could trigger this via IntersectionObserver for scroll)
    animateCounters();

    // 6. Rating star component
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(container => {
        const stars = container.querySelectorAll('.stars i');
        const hiddenInput = container.querySelector('input[type="hidden"]');
        
        stars.forEach(star => {
            star.addEventListener('mouseover', function() {
                const value = this.getAttribute('data-value');
                highlightStars(stars, value);
            });
            
            star.addEventListener('mouseout', function() {
                const currentVal = hiddenInput.value || 0;
                highlightStars(stars, currentVal);
            });
            
            star.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                hiddenInput.value = value;
                highlightStars(stars, value);
            });
        });
    });

    function highlightStars(stars, value) {
        stars.forEach(star => {
            if (star.getAttribute('data-value') <= value) {
                star.classList.add('filled');
                star.classList.replace('far', 'fas'); // FontAwesome solid
            } else {
                star.classList.remove('filled');
                star.classList.replace('fas', 'far'); // FontAwesome regular
            }
        });
    }

    // 7. Form validation helpers (shake animation on invalid)
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Add shake animation to invalid fields
                const invalidInputs = form.querySelectorAll(':invalid');
                invalidInputs.forEach(input => {
                    input.parentElement.classList.add('shake');
                    setTimeout(() => input.parentElement.classList.remove('shake'), 500);
                });
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 8. Confirm delete dialogs
    document.querySelectorAll('.confirm-action').forEach(btn => {
        btn.addEventListener('click', e => {
            const message = btn.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 9. AI Diagnosis AJAX Handler
    const aiTextarea = document.getElementById('problem-description');
    const aiPanel = document.getElementById('ai-panel');
    let debounceTimer;

    if (aiTextarea && aiPanel) {
        aiTextarea.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            const text = this.value.trim();
            
            if (text.length < 10) {
                // Not enough text to diagnose
                return;
            }

            debounceTimer = setTimeout(async () => {
                aiPanel.classList.add('loading');
                try {
                    const response = await fetch('/api/diagnose', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ text })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        updateAiPanel(data);
                    }
                } catch (error) {
                    console.error('AI Diagnosis failed:', error);
                } finally {
                    aiPanel.classList.remove('loading');
                }
            }, 600); // 600ms debounce
        });
    }

    function updateAiPanel(data) {
        const suggestionEl = document.getElementById('ai-service');
        const confidenceBar = document.getElementById('ai-confidence');
        const urgencyEl = document.getElementById('ai-urgency');
        
        if (suggestionEl) suggestionEl.textContent = data.suggested_service;
        if (confidenceBar) confidenceBar.style.width = `${data.confidence}%`;
        if (urgencyEl) urgencyEl.textContent = data.urgency;
        
        const useBtn = document.getElementById('use-suggestion-btn');
        if (useBtn) {
            useBtn.onclick = () => {
                const serviceSelect = document.getElementById('service-type');
                if (serviceSelect) {
                    // Find and select the option that matches
                    for(let i=0; i<serviceSelect.options.length; i++) {
                        if(serviceSelect.options[i].text === data.suggested_service || 
                           serviceSelect.options[i].value === data.suggested_service_id) {
                            serviceSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            };
        }
    }

    // 10. Parts Selection Logic
    const partCheckboxes = document.querySelectorAll('.part-checkbox');
    const labourInput = document.getElementById('labour-cost');
    const commissionRateInput = document.getElementById('commission-rate');
    
    if (partCheckboxes.length > 0) {
        const calculateTotals = () => {
            let partsTotal = 0;
            
            partCheckboxes.forEach(cb => {
                const qtyInput = document.getElementById(`qty-${cb.value}`);
                if (cb.checked) {
                    qtyInput.style.display = 'block';
                    const price = parseFloat(cb.getAttribute('data-price') || 0);
                    const qty = parseInt(qtyInput.value || 1);
                    partsTotal += (price * qty);
                } else {
                    qtyInput.style.display = 'none';
                }
            });
            
            const labour = parseFloat(labourInput?.value || 0);
            const total = partsTotal + labour;
            const rate = parseFloat(commissionRateInput?.value || 0.1);
            const commission = total * rate;
            
            const totalEl = document.getElementById('display-total');
            const commEl = document.getElementById('display-commission');
            
            if (totalEl) totalEl.textContent = `₹${total.toFixed(2)}`;
            if (commEl) commEl.textContent = `₹${commission.toFixed(2)}`;
        };

        partCheckboxes.forEach(cb => cb.addEventListener('change', calculateTotals));
        document.querySelectorAll('.part-qty').forEach(input => input.addEventListener('input', calculateTotals));
        if (labourInput) labourInput.addEventListener('input', calculateTotals);
        
        // Initial calculation
        calculateTotals();
    }
    
    // 11. Image lazy loading
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    }
    
    // 12. Search / Filter live filtering for garage cards
    const searchInput = document.getElementById('garage-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.garage-card');
            
            cards.forEach(card => {
                const name = card.getAttribute('data-name')?.toLowerCase() || '';
                const location = card.getAttribute('data-location')?.toLowerCase() || '';
                
                if (name.includes(term) || location.includes(term)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Add page transition fade-in
    document.body.style.opacity = 0;
    document.body.style.transition = 'opacity 0.5s ease';
    setTimeout(() => document.body.style.opacity = 1, 100);
});
