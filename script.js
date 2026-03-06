const tg = window.Telegram.WebApp;
const orderBtn = document.getElementById('orderBtn');
const cartBadge = document.getElementById('cartBadge');
const cartCount = document.getElementById('cartCount');
const scrollHint = document.getElementById('scrollHint');
const container = document.getElementById('servicesContainer');

tg.expand();
tg.ready();

let cart = {}; // { "Name": { quantity, price } }

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
        if (!res.ok) throw new Error(`Server xatosi: ${res.status}`);
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
            const unit = svc.unit || 'dona';
            const cardId = svc.name.replace(/\s+/g, '-');

            html += `
                <div class="card" id="card-${cardId}" onclick="handleCardClick(event, this, '${svc.name}', ${svc.price})" style="animation-delay: ${delay}s">
                    <div class="check-badge">✅</div>
                    <h3>${svc.name} <span class="price">${formatPrice(svc.price)} so'm / ${unit}</span></h3>
                    <p>${svc.desc}</p>
                    ${tag}
                    <div class="quantity-controls" onclick="event.stopPropagation()">
                        <button class="qty-btn" onclick="updateQty('${svc.name}', -1, ${svc.price})">−</button>
                        <input type="number" class="qty-input" id="qty-${cardId}" value="0" 
                               onchange="setQty('${svc.name}', this.value, ${svc.price})"
                               onfocus="this.select()">
                        <button class="qty-btn" onclick="updateQty('${svc.name}', 1, ${svc.price})">+</button>
                    </div>
                </div>`;
            delay += 0.05;
        });

        html += '</div>';
    });

    html += '<div style="height: 120px;"></div>';
    container.innerHTML = html;
}

function handleCardClick(event, el, name, price) {
    if (event.target.closest('.quantity-controls')) return;

    if (cart[name]) {
        delete cart[name];
        el.classList.remove('selected');
        document.getElementById(`qty-${name.replace(/\s+/g, '-')}`).value = 0;
    } else {
        // Default quantity
        let defaultQty = 1;
        if (name.includes('Vizitka') || name.includes('Flayer')) defaultQty = 100;

        cart[name] = { quantity: defaultQty, price: price };
        el.classList.add('selected');
        document.getElementById(`qty-${name.replace(/\s+/g, '-')}`).value = defaultQty;
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    }
    updateUI();
}

function updateQty(name, delta, price) {
    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');

    if (!cart[name]) {
        cart[name] = { quantity: 0, price: price };
        document.getElementById(`card-${name.replace(/\s+/g, '-')}`).classList.add('selected');
    }

    // Step size
    let step = 1;
    if (name.includes('Vizitka') || name.includes('Flayer')) step = 50;
    if (name.includes('A4')) step = 10;

    cart[name].quantity += delta * step;

    if (cart[name].quantity <= 0) {
        cart[name].quantity = 0;
        delete cart[name];
        document.getElementById(`card-${name.replace(/\s+/g, '-')}`).classList.remove('selected');
    }

    document.getElementById(`qty-${name.replace(/\s+/g, '-')}`).value = cart[name] ? cart[name].quantity : 0;
    updateUI();
}

function setQty(name, val, price) {
    let q = parseInt(val) || 0;
    const cardEl = document.getElementById(`card-${name.replace(/\s+/g, '-')}`);

    if (q <= 0) {
        q = 0;
        delete cart[name];
        if (cardEl) cardEl.classList.remove('selected');
    } else {
        cart[name] = { quantity: q, price: price };
        if (cardEl) cardEl.classList.add('selected');
    }

    const qtyInput = document.getElementById(`qty-${name.replace(/\s+/g, '-')}`);
    if (qtyInput) qtyInput.value = q;
    updateUI();
}

function updateUI() {
    let total = 0;
    let count = 0;

    for (const name in cart) {
        total += cart[name].quantity * cart[name].price;
        count++;
    }

    if (count > 0) {
        cartBadge.style.display = 'block';
        cartCount.textContent = count;
        if (scrollHint) scrollHint.style.display = 'none';
        orderBtn.style.display = 'block';
        orderBtn.textContent = `BUYURTMA BERISH (${formatPrice(total)} so'm)`;
    } else {
        cartBadge.style.display = 'none';
        orderBtn.style.display = 'none';
    }
}

function sendOrder() {
    let services = [];
    let total = 0;

    for (const name in cart) {
        let q = cart[name].quantity;
        let p = cart[name].price;
        services.push(`${name} (${q} dona)`);
        total += q * p;
    }

    if (services.length === 0) return;
    if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');

    tg.sendData(JSON.stringify({
        services: services,
        total: total
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
