// pricing_simple.js - Упрощенная версия с переходом в чат
document.addEventListener('DOMContentLoaded', async function() {
    const container = document.getElementById('services-container');
    try {
        const response = await fetch('/api/services');
        const services = await response.json();
        container.innerHTML = '';
        services.forEach(service => {
            if (!service.is_active) return;
            const card = document.createElement('div');
            card.className = 'bg-white rounded-xl shadow p-5 border flex flex-col h-full';
            // Форматируем цену
            let priceText = 'Индивидуально';
            try {
                const price = JSON.parse(service.price_range);
                if (price && price.min && price.max) {
                    priceText = `${price.min.toLocaleString('ru-RU')} - ${price.max.toLocaleString('ru-RU')} ₽`;
                }
            } catch {}
            card.innerHTML = `
                <div class="flex-grow">
                    <div class="flex justify-between items-start mb-4">
                        <div class="text-3xl">${service.icon || '⚡'}</div>
                        <span class="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded">Активно</span>
                    </div>
                    <h3 class="text-lg font-bold text-gray-800 mb-2">${service.title || ''}</h3>
                    ${service.short_description ? `<p class="text-gray-600 text-sm mb-4">${service.short_description}</p>` : ''}
                    <div class="mb-4">
                        <div class="text-xl font-bold text-blue-600">${priceText}</div>
                    </div>
                </div>
                <div class="mt-auto pt-4">
                    <button 
                        onclick="window.location.href='/dashboard?service=${service.id}'" 
                        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg"
                    >
                        Подать заявку
                    </button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        container.innerHTML = '<p class="text-red-500 text-center">Ошибка загрузки</p>';
    }
});
