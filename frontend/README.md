# Полный метч · веб-виджет

Vite и TypeScript. Приложение открывается на [localhost:3000](http://localhost:3000) и обращается к Django на `http://localhost:8000`.

```sh
npm ci
npm run dev
npm run build
```

Используйте Node.js 22.12 или новее. При другом адресе Django задайте `VITE_API_URL` в `.env.local`.

| Файл | Назначение |
| --- | --- |
| `src/main.ts` | Вход в приложение и переключение между авторизацией, чатом и кабинетом |
| `src/catalog.ts` | Главный каталог и действия с питомцами |
| `src/subscription.ts` | Демо-оформление опеки |
| `src/chat.ts`, `src/chat-window.ts` | Сценарии диалога и управление окном |
| `src/questionnaire.ts` | Вопросы и правила подбора |
| `src/auth.ts`, `src/account.ts` | Авторизация и вкладка «Мои подопечные» |
| `src/pet-card.ts` | Общая карточка питомца |
| `src/api.ts` | Запросы к Django |
| `src/styles/`, `public/static/` | Стили и публичные ресурсы |

`npm run build` проверяет типы и собирает сайт в `dist`. Рабочие фотографии животных приходят с бэкенда по адресам `/media/`.
