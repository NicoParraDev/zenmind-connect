/**
 * ZenMindConnect 2.0 - Interactive Features
 * Mejoras de interactividad y UX
 * Incluye protección anti-bot
 */

(function() {
    'use strict';
    
    // ============================================
    // PROTECCIÓN ANTI-BOT: Token de JavaScript
    // ============================================
    // Establece un token que indica que JavaScript está activo
    // Esto ayuda al middleware a detectar bots que no ejecutan JS
    (function() {
        // Establecer cookie para verificación
        document.cookie = 'js_enabled=1; path=/; SameSite=Lax; max-age=3600';
        
        // Interceptar XMLHttpRequest
        if (typeof XMLHttpRequest !== 'undefined') {
            const originalOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
                this.addEventListener('loadstart', function() {
                    this.setRequestHeader('X-JS-Token', 'active');
                });
                return originalOpen.apply(this, arguments);
            };
        }
        
        // Interceptar fetch API
        if (typeof fetch !== 'undefined') {
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                options = options || {};
                options.headers = options.headers || {};
                if (options.headers instanceof Headers) {
                    options.headers.set('X-JS-Token', 'active');
                } else {
                    options.headers['X-JS-Token'] = 'active';
                }
                return originalFetch.apply(this, arguments);
            };
        }
        
        // Agregar token a todos los formularios
        document.addEventListener('DOMContentLoaded', function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(function(form) {
                // Crear campo hidden con token
                let tokenField = form.querySelector('input[name="js_token"]');
                if (!tokenField) {
                    tokenField = document.createElement('input');
                    tokenField.type = 'hidden';
                    tokenField.name = 'js_token';
                    tokenField.value = 'active';
                    form.appendChild(tokenField);
                }
            });
        });
    })();

    // ============================================
    // LOADING STATES
    // ============================================
    
    function showLoading(button) {
        if (!button) return;
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
        button.classList.add('loading');
    }

    function hideLoading(button) {
        if (!button || !button.dataset.originalText) return;
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
        button.classList.remove('loading');
    }

    // Auto-loading en formularios
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !form.dataset.noLoading) {
                    showLoading(submitBtn);
                }
            });
        });
    });

    // ============================================
    // VALIDACIÓN EN TIEMPO REAL
    // ============================================
    
    function validateField(field) {
        const value = field.value.trim();
        const fieldType = field.type || field.tagName.toLowerCase();
        const fieldName = field.name || field.id;
        let isValid = true;
        let errorMessage = '';

        // Remover clases previas
        field.classList.remove('is-valid', 'is-invalid');
        const errorDiv = field.parentElement.querySelector('.field-error');
        if (errorDiv) errorDiv.remove();

        // Validaciones según tipo
        if (field.required && !value) {
            isValid = false;
            errorMessage = 'Este campo es obligatorio';
        } else if (fieldType === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Ingresa un email válido';
            }
        } else if (fieldName.toLowerCase().includes('password') && value) {
            if (value.length < 8) {
                isValid = false;
                errorMessage = 'La contraseña debe tener al menos 8 caracteres';
            }
        } else if (fieldName.toLowerCase().includes('telefono') && value) {
            const phoneRegex = /^\+?56\s?9\s?\d{8}$/;
            if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                isValid = false;
                errorMessage = 'Formato: +56 9 12345678';
            }
        } else if (fieldName.toLowerCase().includes('rut') && value) {
            // Validación básica de RUT chileno
            const rutRegex = /^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$/;
            if (!rutRegex.test(value)) {
                isValid = false;
                errorMessage = 'Formato: 12.345.678-9';
            }
        }

        // Aplicar clases y mensaje
        if (value) {
            field.classList.add(isValid ? 'is-valid' : 'is-invalid');
            if (!isValid) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'field-error';
                errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${errorMessage}`;
                field.parentElement.appendChild(errorDiv);
            }
        }

        return isValid;
    }

    // Validación en tiempo real
    document.addEventListener('DOMContentLoaded', function() {
        const inputs = document.querySelectorAll('input[required], textarea[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });

    // ============================================
    // ANIMACIONES DE ENTRADA
    // ============================================
    
    function animateOnScroll() {
        const elements = document.querySelectorAll('.fade-in, .slide-in, .card, .admin-action-card');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        elements.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            observer.observe(el);
        });
    }

    document.addEventListener('DOMContentLoaded', animateOnScroll);

    // ============================================
    // FEEDBACK VISUAL EN BOTONES
    // ============================================
    
    document.addEventListener('DOMContentLoaded', function() {
        const buttons = document.querySelectorAll('.btn:not(.no-ripple)');
        buttons.forEach(button => {
            button.addEventListener('click', function(e) {
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                ripple.classList.add('ripple');
                
                this.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
        });
    });

    // ============================================
    // TOOLTIPS MEJORADOS
    // ============================================
    
    function initTooltips() {
        const elements = document.querySelectorAll('[data-tooltip]');
        elements.forEach(el => {
            el.addEventListener('mouseenter', function(e) {
                const tooltip = document.createElement('div');
                tooltip.className = 'zenmind-tooltip';
                tooltip.textContent = this.dataset.tooltip;
                document.body.appendChild(tooltip);
                
                const rect = this.getBoundingClientRect();
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
                
                this._tooltip = tooltip;
            });
            
            el.addEventListener('mouseleave', function() {
                if (this._tooltip) {
                    this._tooltip.remove();
                    this._tooltip = null;
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', initTooltips);

    // ============================================
    // SMOOTH SCROLL
    // ============================================
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ============================================
    // CONFIRMACIÓN DE ACCIONES DESTRUCTIVAS
    // ============================================
    
    document.querySelectorAll('a[data-confirm], button[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirm || '¿Estás seguro?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // ============================================
    // AUTO-FOCUS EN FORMULARIOS
    // ============================================
    
    document.querySelectorAll('form').forEach(form => {
        const firstInput = form.querySelector('input:not([type="hidden"]), textarea, select');
        if (firstInput && !form.dataset.noAutofocus) {
            setTimeout(() => firstInput.focus(), 100);
        }
    });

    // ============================================
    // MEJORA DE NAVEGACIÓN MOBILE
    // ============================================
    
    function closeMobileMenuOnClick() {
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        const navbar = document.getElementById('navbarNav');
        
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 768 && navbar && navbar.classList.contains('active')) {
                    navbar.classList.remove('active');
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', closeMobileMenuOnClick);

    // ============================================
    // MEJORA DE FORMULARIOS CON AUTO-SAVE DRAFT
    // ============================================
    
    function initAutoSave() {
        const forms = document.querySelectorAll('form[data-autosave]');
        forms.forEach(form => {
            const formId = form.id || 'form-' + Math.random().toString(36).substr(2, 9);
            form.id = formId;
            
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                const key = formId + '-' + (input.name || input.id);
                const saved = localStorage.getItem(key);
                if (saved) {
                    input.value = saved;
                }
                
                input.addEventListener('input', function() {
                    localStorage.setItem(key, this.value);
                });
            });
            
            form.addEventListener('submit', function() {
                inputs.forEach(input => {
                    const key = formId + '-' + (input.name || input.id);
                    localStorage.removeItem(key);
                });
            });
        });
    }

    document.addEventListener('DOMContentLoaded', initAutoSave);

    // ============================================
    // NOTIFICACIONES TOAST
    // ============================================
    
    window.showToast = function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `zenmind-toast zenmind-toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };

    // ============================================
    // LAZY LOADING DE IMÁGENES
    // ============================================
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // ============================================
    // COPY TO CLIPBOARD
    // ============================================
    
    document.querySelectorAll('[data-copy]').forEach(element => {
        element.addEventListener('click', async function() {
            const text = this.dataset.copy;
            try {
                await navigator.clipboard.writeText(text);
                showToast('Copiado al portapapeles', 'success');
            } catch (err) {
                showToast('Error al copiar', 'error');
            }
        });
    });

})();

