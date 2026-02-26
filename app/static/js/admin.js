// Основные функции админки
function setupTabSwitching() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    console.log("Найдено кнопок:", tabButtons.length, "вкладок:", tabContents.length);
    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            const tabId = button.getAttribute("data-tab");
            console.log("Кнопка нажата, data-tab:", tabId);
            // Убираем активный класс у всех кнопок
            tabButtons.forEach(btn => {
                btn.classList.remove("text-blue-600", "bg-blue-50");
                btn.classList.add("text-gray-700");
            });
            // Добавляем активный класс текущей кнопке
            button.classList.add("text-blue-600", "bg-blue-50");
            button.classList.remove("text-gray-700");
            // Скрываем все вкладки
            tabContents.forEach(content => {
                content.classList.add("hidden");
            });
            // Показываем выбранную вкладку
            const activeTab = document.getElementById(tabId + "-tab");
            if (activeTab) {
                activeTab.classList.remove("hidden");
                console.log("Показана вкладка:", tabId);
            }
        });
    });
    // Активируем первую вкладку
    if (tabButtons.length > 0) {
        tabButtons[0].click();
        console.log("Активируем первую вкладку");
    }
}
// Обработчик для кнопки выхода
function setupLogoutButton() {
    const logoutBtn = document.querySelector("a[href*='/api/auth/logout']");
    if (logoutBtn) {
        // Удаляем старые обработчики если есть
        logoutBtn.replaceWith(logoutBtn.cloneNode(true));
        const newLogoutBtn = document.querySelector("a[href*='/api/auth/logout']");
        newLogoutBtn.addEventListener("click", async function(e) {
            e.preventDefault();
            console.log("Выход: запрос на сервер...");
            try {
                const response = await fetch(this.href, {
                    method: "GET",
                    credentials: "include"
                });
                console.log("Выход: статус ответа", response.status);
                if (response.ok) {
                    // Перенаправляем на главную страницу
                    window.location.href = "/";
                } else {
                    window.location.href = "/";
                }
            } catch (error) {
                console.error("Ошибка при выходе:", error);
                window.location.href = "/";
            }
        });
        console.log("Обработчик выхода настроен");
    }
}
// Инициализация при загрузке страницы
document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM полностью загружен");
    setupTabSwitching();
    setupLogoutButton();
});
console.log("admin.js загружен");
