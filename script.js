const tg = window.Telegram.WebApp;
const orderBtn = document.getElementById('orderBtn');
const cartBadge = document.getElementById('cartBadge');
const cartCount = document.getElementById('cartCount');
const scrollHint = document.getElementById('scrollHint');
const container = document.getElementById('servicesContainer');

tg.expand();
tg.ready();

let selectedServices = [];
let totalPrice = 0;

// Scroll hint
window.addEventListener('scroll', () => {
    if (window.scrollY > 100 && scrollHint) {
        scrollHint.style.opacity = '0';
        setTimeout(() => scrollHint.style.display = 'none', 500);
    }
});

function formatPrice(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

// prices.json dan narxlarni yuklash
async function loadPrices() {
    try {
        const res = await fetch('prices.json?t=' + Date.now());
        const data = await res.json();
        renderServices(data.categories);
    } catch (e) {
        console.error('Narxlarni yuklashda xato:', e);
        container.innerHTML = `<p style="text-align:center;color:#ef4444;">❌ Narxlarni yuklashda xatolik<br><small>${e.message}</small></p>`;
    }
}

function renderServices(categories) {
    let html = '';
    let delay = 0.1;

    categories.forEach(cat => {
        html += `<h2 class="section-title">${cat.title}</h2><div class="grid">`;

        cat.services.forEach(svc => {
            const tag = svc.tag ? `<div class="tag">${svc.tag}</div>` : '';
            html += `
                <div class="card" onclick="selectService(this, '${svc.name}', ${svc.price})" style="animation-delay: ${delay}s">
                    <div class="check-badge">✅</div>
                    <h3>${svc.name} <span class="price">${formatPrice(svc.price)} so'm</span></h3>
                    <p>${svc.desc}</p>
                    ${tag}
                </div>`;
            delay += 0.05;
        });

        html += '</div>';
    });

    html += '<div style="height: 120px;"></div>';
    container.innerHTML = html;
}

function selectService(el, name, price) {
    const existingIndex = selectedServices.indexOf(name);

    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');

    if (existingIndex > -1) {
        selectedServices.splice(existingIndex, 1);
        totalPrice -= price;
        el.classList.remove('selected');
    } else {
        selectedServices.push(name);
        totalPrice += price;
        el.classList.add('selected');
    }

    updateUI();
}

function updateUI() {
    if (selectedServices.length > 0) {
        cartBadge.style.display = 'block';
        cartCount.textContent = selectedServices.length;
        if (scrollHint) scrollHint.style.display = 'none';
        orderBtn.style.display = 'block';
        orderBtn.textContent = `BUYURTMA BERISH (${formatPrice(totalPrice)} so'm)`;
    } else {
        cartBadge.style.display = 'none';
        orderBtn.style.display = 'none';
    }
}

function sendOrder() {
    if (selectedServices.length === 0) return;
    if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');

    tg.sendData(JSON.stringify({
        services: selectedServices,
        total: totalPrice
    }));
    tg.close();
}

// Telegram mavzusiga moslashish
if (tg.themeParams) {
    if (tg.themeParams.bg_color) document.body.style.setProperty('--bg', tg.themeParams.bg_color);
    if (tg.themeParams.text_color) document.body.style.setProperty('--text', tg.themeParams.text_color);
}

// Sahifa yuklanganda narxlarni olish
loadPrices();
