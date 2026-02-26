// pricing.js - Версия с переходом в чат при нажатии кнопки
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Загрузка страницы цен...');
    const container = document.getElementById('services-container');
    try {
        // Загружаем данные
        const response = await fetch('/api/services');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const services = await response.json();
        console.log(`Получено ${services.length} услуг`);
        // Очищаем контейнер
        container.innerHTML = '';
        // Если нет услуг
        if (!services || services.length === 0) {
            container.innerHTML = `
                <div class="col-span-4 text-center py-12">
                    <div class="max-w-md mx-auto p-6 bg-yellow-50 rounded-lg border border-yellow-200">
                        <p class="text-yellow-700 font-medium">Услуги временно недоступны</p>
                        <p class="text-gray-600 text-sm mt-2">Попробуйте обновить страницу позже</p>
                    </div>
                </div>
            `;
            return;
        }
        // Создаем карточки
        services.forEach(service => {
            if (!service.is_active) return;
            const card = createServiceCard(service);
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        showError(container, error.message);
    }
});
function createServiceCard(service) {
    // Форматируем данные
    const priceText = formatPrice(service.price_range);
    const durationText = formatDuration(service.duration);
    const features = extractFeatures(service);
    // Создаем карточку
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-200 flex flex-col h-full';
    // Особенности
    let featuresHtml = '';
    if (features.length > 0) {
        const featuresList = features.slice(0, 3).map(feature => 
            `<li class="flex items-start text-sm text-gray-600 mb-2">
                <span class="text-green-500 mr-2 mt-0.5 flex-shrink-0">✓</span>
                <span class="flex-1">${escapeHtml(feature)}</span>
            </li>`
        ).join('');
        const moreCount = features.length > 3 ? features.length - 3 : 0;
        const moreHtml = moreCount > 0 ? 
            `<li class="text-gray-400 text-xs text-center mt-2">+ ещё ${moreCount} пункта</li>` : '';
        featuresHtml = `
            <div class="mt-4 pt-4 border-t border-gray-100">
                <h4 class="font-medium text-gray-700 mb-3 text-sm">Включает:</h4>
                <ul>
                    ${featuresList}
                    ${moreHtml}
                </ul>
            </div>`;
    }
    card.innerHTML = `
        <div class="p-5 flex-grow">
            <!-- Заголовок и статус -->
            <div class="flex justify-between items-start mb-4">
                <div class="text-3xl">${service.icon || '⚡'}</div>
                <span class="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">Активно</span>
            </div>
            <!-- Название и описание -->
            <h3 class="text-lg font-bold text-gray-800 mb-2">${escapeHtml(service.title || '')}</h3>
            ${service.short_description ? 
                `<p class="text-gray-600 text-sm mb-4 leading-relaxed">${escapeHtml(service.short_description)}</p>` : ''}
            <!-- Цена и срок -->
            <div class="mb-4">
                <div class="text-xl font-bold text-blue-600">${priceText}</div>
                <div class="text-gray-500 text-sm mt-1">${durationText}</div>
            </div>
            <!-- Особенности -->
            ${featuresHtml}
        </div>
        <!-- Кнопка -->
        <div class="p-5 pt-0 mt-auto">
            <button 
                onclick="submitApplication(${service.id}, '${escapeHtml(service.title || '')}')" 
                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 shadow-sm hover:shadow"
            >
                Подать заявку
            </button>
        </div>
    `;
    return card;
}
// Вспомогательные функции
function formatPrice(priceRange) {
    if (!priceRange) return 'Индивидуально';
    try {
        const range = typeof priceRange === 'string' ? JSON.parse(priceRange) : priceRange;
        if (range && range.min !== undefined && range.max !== undefined) {
            const min = new Intl.NumberFormat('ru-RU').format(range.min);
            const max = new Intl.NumberFormat('ru-RU').format(range.max);
            return `${min} - ${max} ₽`;
        }
    } catch {}
    return priceRange;
}
function formatDuration(duration) {
    if (!duration) return 'Срок обсуждается';
    try {
        const dur = typeof duration === 'string' ? JSON.parse(duration) : duration;
        if (dur && dur.min !== undefined && dur.max !== undefined) {
            return `${dur.min}-${dur.max} дней`;
        }
    } catch {}
    return duration;
}
function extractFeatures(service) {
    if (!service.features) return [];
    try {
        const features = typeof service.features === 'string' ? JSON.parse(service.features) : service.features;
        return Array.isArray(features) ? features : [];
    } catch {
        return [];
    }
}
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
function showError(container, message) {
    container.innerHTML = `
        <div class="col-span-4">
            <div class="max-w-md mx-auto p-6 bg-red-50 border border-red-200 rounded-xl text-center">
                <div class="text-red-600 font-medium mb-2">Ошибка загрузки</div>
                <p class="text-gray-600 text-sm mb-4">${escapeHtml(message)}</p>
                <button onclick="location.reload()" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Обновить страницу →
                </button>
            </div>
        </div>
    `;
}
// Функция для подачи заявки - переход в чат с разработчиком
function submitApplication(serviceId, serviceTitle) {
    console.log(`Подача заявки на услугу: ${serviceTitle} (ID: ${serviceId})`);
    // Сохраняем информацию о выбранной услуге
    localStorage.setItem('selectedService', JSON.stringify({
        id: serviceId,
        title: serviceTitle,
        timestamp: new Date().toISOString(),
        action: 'application'
    }));
    // Проверяем, авторизован ли пользователь
    checkAuthAndRedirect(serviceId, serviceTitle);
}
// Проверка авторизации и редирект
function checkAuthAndRedirect(serviceId, serviceTitle) {
    // Пытаемся получить информацию о пользователе
    fetch('/api/auth/me', {
        credentials: 'include' // Важно для отправки cookies
    })
    .then(response => {
        if (response.ok) {
            // Пользователь авторизован - переходим в чат
            return response.json().then(userData => {
                console.log('Пользователь авторизован:', userData.email);
                redirectToChat(serviceId, serviceTitle, userData.id);
            });
        } else {
            // Пользователь не авторизован - просим войти
            console.log('Пользователь не авторизован, требуется вход');
            redirectToLogin(serviceId, serviceTitle);
        }
    })
    .catch(error => {
        console.error('Ошибка проверки авторизации:', error);
        // В случае ошибки тоже просим войти
        redirectToLogin(serviceId, serviceTitle);
    });
}
// Переход в чат
function redirectToChat(serviceId, serviceTitle, userId) {
    // Сохраняем сообщение о выбранной услуге
    const serviceMessage = `🔔 Новая заявка на услугу: ${serviceTitle}`;
    localStorage.setItem('initialChatMessage', serviceMessage);
    // Переходим в чат
    console.log(`Переход в чат для пользователя ${userId} с услугой ${serviceId}`);
    window.location.href = `/dashboard?service=${serviceId}&action=application`;
}
// Переход на страницу входа с редиректом обратно
function redirectToLogin(serviceId, serviceTitle) {
    // Сохраняем информацию для после входа
    const redirectData = {
        serviceId: serviceId,
        serviceTitle: serviceTitle,
        timestamp: new Date().toISOString(),
        redirectTo: 'chat'
    };
    localStorage.setItem('pendingApplication', JSON.stringify(redirectData));
    // Показываем сообщение и переходим на страницу входа
    alert('Для подачи заявки необходимо войти в систему');
    window.location.href = `/login?redirect=/pricing&action=apply&service=${serviceId}`;
}
// Проверяем есть ли ожидающая заявка при загрузке страницы
function checkPendingApplication() {
    const pendingApp = localStorage.getItem('pendingApplication');
    if (pendingApp) {
        try {
            const data = JSON.parse(pendingApp);
            console.log('Найдена ожидающая заявка:', data);
            // Если пользователь сейчас на странице цен, можно показать уведомление
            if (window.location.pathname === '/pricing') {
                console.log('Пользователь вернулся на страницу цен после входа');
                // Можно показать toast-уведомление
                showNotification('Теперь вы можете подать заявку на выбранную услугу!');
            }
            // Очищаем pending application
            localStorage.removeItem('pendingApplication');
        } catch (e) {
            console.error('Ошибка парсинга pendingApplication:', e);
        }
    }
}
// Показ уведомления
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 opacity-0 transition-opacity duration-300';
    notification.textContent = message;
    notification.id = 'notification';
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.add('opacity-100');
    }, 10);
    setTimeout(() => {
        notification.classList.remove('opacity-100');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}
// При загрузке страницы проверяем pending applications
document.addEventListener('DOMContentLoaded', function() {
    checkPendingApplication();
});
