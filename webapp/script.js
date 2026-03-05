const tg = window.Telegram.WebApp;
const orderBtn = document.getElementById('orderBtn');

tg.expand();
tg.MainButton.hide();

let selectedServices = [];
let totalPrice = 0;

function selectService(name, price) {
    const existingIndex = selectedServices.indexOf(name);

    if (existingIndex > -1) {
        selectedServices.splice(existingIndex, 1);
        totalPrice -= price;
        event.currentTarget.classList.remove('selected');
        event.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        event.currentTarget.style.boxShadow = 'none';
    } else {
        selectedServices.push(name);
        totalPrice += price;
        event.currentTarget.classList.add('selected');
        event.currentTarget.style.borderColor = '#00f2fe';
        event.currentTarget.style.boxShadow = '0 0 15px rgba(0, 242, 254, 0.4)';
    }

    if (selectedServices.length > 0) {
        orderBtn.style.display = 'block';
        orderBtn.innerText = `Tanlash (${totalPrice.toLocaleString('uz-UZ')} so'm)`;
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
