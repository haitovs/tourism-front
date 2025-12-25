/**
 * New Year Theme - Toggle & Effects System
 * Toggle ON by default, bottom-right corner
 */

(function() {
    'use strict';

    // Default settings
    const DEFAULT_SETTINGS = {
        enabled: true,
        snow: true,
        glow: true,
        colors: true,
        sparkles: false,
        confetti: false
    };

    // Get settings from localStorage or use defaults
    function getSettings() {
        try {
            const saved = localStorage.getItem('newYearSettings');
            if (saved) {
                return { ...DEFAULT_SETTINGS, ...JSON.parse(saved) };
            }
        } catch (e) {}
        return { ...DEFAULT_SETTINGS };
    }

    // Save settings to localStorage
    function saveSettings(settings) {
        try {
            localStorage.setItem('newYearSettings', JSON.stringify(settings));
        } catch (e) {}
    }

    // Current settings
    let settings = getSettings();

    // ==================== SNOW EFFECT (Canvas) ====================
    let snowCanvas = null;
    let snowAnimationId = null;

    function startSnow() {
        if (snowCanvas) return;
        
        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.id = 'ny-snow-canvas';
        canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99990;';
        document.body.appendChild(canvas);
        snowCanvas = canvas;
        
        const ctx = canvas.getContext('2d');
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;
        
        // Create snowflakes
        const flakes = [];
        const flakeCount = 150;
        
        for (let i = 0; i < flakeCount; i++) {
            flakes.push({
                x: Math.random() * width,
                y: Math.random() * height,
                r: Math.random() * 4 + 1,
                d: Math.random() * flakeCount,
                speed: Math.random() * 1 + 0.5,
                swing: Math.random() * 0.5
            });
        }
        
        // Handle resize
        const resizeHandler = () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        };
        window.addEventListener('resize', resizeHandler);
        canvas._resizeHandler = resizeHandler;
        
        // Animation
        let angle = 0;
        function draw() {
            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.beginPath();
            
            for (let i = 0; i < flakeCount; i++) {
                const f = flakes[i];
                ctx.moveTo(f.x, f.y);
                ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2, true);
            }
            
            ctx.fill();
            
            // Update positions
            angle += 0.01;
            for (let i = 0; i < flakeCount; i++) {
                const f = flakes[i];
                f.y += f.speed;
                f.x += Math.sin(angle + f.d) * f.swing;
                
                // Reset flake to top
                if (f.y > height) {
                    f.y = -10;
                    f.x = Math.random() * width;
                }
            }
            
            snowAnimationId = requestAnimationFrame(draw);
        }
        
        draw();
    }

    function stopSnow() {
        if (snowAnimationId) {
            cancelAnimationFrame(snowAnimationId);
            snowAnimationId = null;
        }
        if (snowCanvas) {
            if (snowCanvas._resizeHandler) {
                window.removeEventListener('resize', snowCanvas._resizeHandler);
            }
            snowCanvas.remove();
            snowCanvas = null;
        }
    }

    // ==================== GLOW EFFECT ====================
    function applyGlow(enable) {
        document.body.classList.toggle('ny-glow', enable);
    }

    // ==================== COLORS EFFECT ====================
    function applyColors(enable) {
        document.body.classList.toggle('ny-colors', enable);
    }

    // ==================== SPARKLES (CURSOR) ====================
    let sparkleHandler = null;

    function createSparkle(x, y) {
        const sparkle = document.createElement('div');
        sparkle.className = 'ny-sparkle';
        sparkle.style.left = x + 'px';
        sparkle.style.top = y + 'px';
        document.body.appendChild(sparkle);
        setTimeout(() => sparkle.remove(), 600);
    }

    function startSparkles() {
        if (sparkleHandler) return;
        let lastTime = 0;
        sparkleHandler = (e) => {
            const now = Date.now();
            if (now - lastTime < 50) return;
            lastTime = now;
            createSparkle(e.clientX, e.clientY);
        };
        document.addEventListener('mousemove', sparkleHandler);
    }

    function stopSparkles() {
        if (sparkleHandler) {
            document.removeEventListener('mousemove', sparkleHandler);
            sparkleHandler = null;
        }
    }

    // ==================== CONFETTI ====================
    function triggerConfetti() {
        for (let i = 0; i < 50; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.className = 'ny-confetti';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.backgroundColor = ['#ff0', '#f0f', '#0ff', '#f00', '#0f0'][Math.floor(Math.random() * 5)];
                confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
                document.body.appendChild(confetti);
                setTimeout(() => confetti.remove(), 4000);
            }, i * 30);
        }
    }

    // ==================== APPLY ALL EFFECTS ====================
    function applyEffects() {
        document.body.classList.toggle('ny-theme-active', settings.enabled);

        if (settings.enabled && settings.snow) startSnow();
        else stopSnow();

        applyGlow(settings.enabled && settings.glow);
        applyColors(settings.enabled && settings.colors);

        if (settings.enabled && settings.sparkles) startSparkles();
        else stopSparkles();
    }

    // ==================== TOGGLE UI ====================
    function createToggleUI() {
        const container = document.createElement('div');
        container.id = 'ny-toggle-container';
        container.innerHTML = `
            <button id="ny-main-toggle" class="ny-toggle-btn" title="New Year Theme">
                🎄
            </button>
            <div id="ny-menu" class="ny-menu">
                <div class="ny-menu-header">
                    <span>🎄 New Year Mode</span>
                    <label class="ny-switch">
                        <input type="checkbox" id="ny-master" ${settings.enabled ? 'checked' : ''}>
                        <span class="ny-slider"></span>
                    </label>
                </div>
                <div class="ny-menu-items">
                    <label class="ny-menu-item">
                        <span>❄️ Snow</span>
                        <input type="checkbox" id="ny-snow" ${settings.snow ? 'checked' : ''}>
                    </label>
                    <label class="ny-menu-item">
                        <span>🌟 Glow</span>
                        <input type="checkbox" id="ny-glow" ${settings.glow ? 'checked' : ''}>
                    </label>
                    <label class="ny-menu-item">
                        <span>🎨 Colors</span>
                        <input type="checkbox" id="ny-colors" ${settings.colors ? 'checked' : ''}>
                    </label>
                    <label class="ny-menu-item">
                        <span>✨ Sparkles</span>
                        <input type="checkbox" id="ny-sparkles" ${settings.sparkles ? 'checked' : ''}>
                    </label>
                    <div class="ny-menu-item ny-confetti-btn" id="ny-confetti">
                        <span>🎁 Confetti</span>
                        <span class="ny-burst-text">🎉 Burst!</span>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(container);

        // Toggle menu visibility
        document.getElementById('ny-main-toggle').addEventListener('click', (e) => {
            e.stopPropagation();
            container.classList.toggle('ny-menu-open');
        });

        // Close menu on outside click
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                container.classList.remove('ny-menu-open');
            }
        });

        // Master toggle
        document.getElementById('ny-master').addEventListener('change', (e) => {
            settings.enabled = e.target.checked;
            saveSettings(settings);
            applyEffects();
        });

        // Individual toggles (persistent ones)
        ['snow', 'glow', 'colors', 'sparkles'].forEach(key => {
            document.getElementById('ny-' + key).addEventListener('change', (e) => {
                settings[key] = e.target.checked;
                saveSettings(settings);
                applyEffects();
            });
        });

        // Confetti is a one-shot button, not a toggle
        document.getElementById('ny-confetti').addEventListener('click', (e) => {
            if (settings.enabled) {
                triggerConfetti();
            }
        });
    }

    function updateToggleUI() {
        const confettiCheck = document.getElementById('ny-confetti');
        if (confettiCheck) confettiCheck.checked = settings.confetti;
    }

    // ==================== INIT ====================
    function init() {
        createToggleUI();
        applyEffects();
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
