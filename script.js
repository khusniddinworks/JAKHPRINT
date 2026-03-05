const tg = window.Telegram.WebApp;
const orderBtn = document.getElementById('orderBtn');

tg.expand();
tg.ready();

let selectedServices = [];
let totalPrice = 0;

function selectService(el, name, price) {
    const existingIndex = selectedServices.indexOf(name);

    // Haptic feedback (Vibratsiya)
    if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');

    if (existingIndex > -1) {
        selectedServices.splice(existingIndex, 1);
        totalPrice -= price;
        el.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        el.style.boxShadow = 'none';
        el.classList.remove('selected');
    } else {
        selectedServices.push(name);
        totalPrice += price;
        el.style.borderColor = '#00f2fe';
        el.style.boxShadow = '0 0 15px rgba(0, 242, 254, 0.4)';
        el.classList.add('selected');
    }

    if (selectedServices.length > 0) {
        orderBtn.style.display = 'block';
        orderBtn.innerText = `TANLASH (${totalPrice.toLocaleString('uz-UZ').replace(/,/g, ' ')} so'm)`;
    } else {
        orderBtn.style.display = 'none';
    }
}

function sendOrder() {
    if (selectedServices.length === 0) return;

    const data = {
        services: selectedServices,
        total: totalPrice
    };

    // Telegramga ma'lumotni yuborish
    tg.sendData(JSON.stringify(data));
    tg.close();
}

// Telegram mavzusiga moslashish (Ixtiyoriy)
document.body.style.setProperty('--bg', tg.themeParams.bg_color || '#0f172a');
document.body.style.setProperty('--text', tg.themeParams.text_color || '#f8fafc');
