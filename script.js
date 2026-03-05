const tg = window.Telegram.WebApp;
const orderBtn = document.getElementById('orderBtn');
const cartBadge = document.getElementById('cartBadge');
const cartCount = document.getElementById('cartCount');
const scrollHint = document.getElementById('scrollHint');

tg.expand();
tg.ready();

let selectedServices = [];
let totalPrice = 0;

// Scroll hint — pastga sursalar yo'qoladi
window.addEventListener('scroll', () => {
    if (window.scrollY > 100 && scrollHint) {
        scrollHint.style.opacity = '0';
        setTimeout(() => scrollHint.style.display = 'none', 500);
    }
});

function formatPrice(num) {
    return num.toLocaleString('uz-UZ').replace(/,/g, ' ');
}

function selectService(el, name, price) {
    const existingIndex = selectedServices.indexOf(name);

    // Haptic feedback
    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('light');
    }

    if (existingIndex > -1) {
        // Olib tashlash
        selectedServices.splice(existingIndex, 1);
        totalPrice -= price;
        el.classList.remove('selected');
    } else {
        // Qo'shish
        selectedServices.push(name);
        totalPrice += price;
        el.classList.add('selected');
    }

    updateUI();
}

function updateUI() {
    // Cart badge
    if (selectedServices.length > 0) {
        cartBadge.style.display = 'block';
        cartCount.textContent = selectedServices.length;

        // Scroll hint yashirish
        if (scrollHint) scrollHint.style.display = 'none';

        // Buyurtma tugmasi
        orderBtn.style.display = 'block';
        orderBtn.textContent = `BUYURTMA BERISH (${formatPrice(totalPrice)} so'm)`;
    } else {
        cartBadge.style.display = 'none';
        orderBtn.style.display = 'none';
    }
}

function sendOrder() {
    if (selectedServices.length === 0) return;

    // Haptic
    if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
    }

    const data = {
        services: selectedServices,
        total: totalPrice
    };

    tg.sendData(JSON.stringify(data));
    tg.close();
}

// Telegram mavzusiga moslashish
if (tg.themeParams) {
    const bg = tg.themeParams.bg_color;
    const text = tg.themeParams.text_color;
    if (bg) document.body.style.setProperty('--bg', bg);
    if (text) document.body.style.setProperty('--text', text);
}
