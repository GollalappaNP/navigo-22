(() => {
    console.log('NAVIGo UI helpers ready');

    // PWA: register service worker (root scope via /sw.js route)
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js').catch((err) => {
                console.warn('Service worker registration failed:', err);
            });
        });
    }

    const navLinks = document.querySelectorAll('.nav-links a, .nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotSidebar = document.querySelector('.chatbot-sidebar');
    if (chatbotToggle && chatbotSidebar) {
        chatbotToggle.addEventListener('click', () => {
            chatbotSidebar.classList.toggle('open');
        });
    }
})();






