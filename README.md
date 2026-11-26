# Pet Shelter · «Полный метч»

```text
Pet Shelter/
├── backend/    Django, SQLite, API, media и сборка статики
└── frontend/   Vite и TypeScript
```

Деплой использует этот репозиторий. Веб-виджет основан на [FullMatchWeb](https://github.com/Aucuneentie/FullMatchWeb). Исходная React-заготовка хранится в `examples/react-starter`.

## Запуск

В первом терминале из папки проекта запустите Django.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
test -f backend/.env || cp backend/.env.example backend/.env
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py runserver localhost:8000
```

Если виртуальное окружение уже установлено на Windows, запустите команды из корня проекта в PowerShell.

```powershell
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py runserver
```

Для локального `manage.py` доступен ключ разработки. `DJANGO_SECRET_KEY` нужен Django для подписи сессий и других данных приложения. На сервере задайте собственный ключ в окружении.

Во втором терминале из папки проекта запустите фронтенд на Node.js 22.12+.

```sh
cd frontend
npm ci
npm run dev
```

Откройте [виджет](http://localhost:3000). Django доступен на [localhost:8000](http://localhost:8000/api/animals/), его [админка](http://localhost:8000/admin/) позволяет добавлять питомцев и загружать фото.

## Где лежат файлы

- `frontend/src` — интерфейс, чат, авторизация, личный кабинет, API-клиент, карточки и стили. `frontend/public/static` содержит сборочные ресурсы вроде логотипа виджета. `npm run build` создаёт сайт в `frontend/dist`, скрипты и стили попадают в `dist/static`.
- `backend/media` — фотографии, которые загружают через админку или копируют из Битрикс24. В БД хранится путь к фото. Локально Django раздаёт их по `/media/`. На сервере сохраняйте эту папку между релизами и настройте её отдачу по тому же пути.
- `backend/staticfiles` — статика Django, которую собирает `.venv/bin/python backend/manage.py collectstatic`. На сервере она доступна под `/static/` на адресе бэкенда.

Каталог на главной загружается из Django. Кнопка «Забрать домой» открывает контакты приюта. Демо-оплата опеки записывает подписку в Django, питомец появляется в «Мои подопечные». У каждого питомца может быть до пяти активных опекунов. Демо-оплата работает без списания денег.

## Битрикс24

- [Как создать вебхук в интерфейсе Битрикс24](backend/docs/BITRIX24_WEBHOOK.md)
- [Переменные окружения и запуск импорта](backend/docs/BITRIX24_SETUP.md)

## ИИ-помощник

Задайте `OPENROUTER_TOKEN` или `OPENROUTER_API_KEY` в `.env` в корне проекта или в `backend/.env`. Сначала Django читает переменные процесса, затем файл в корне проекта и после него файл в `backend`. Модель для текста задаёт `OPENROUTER_MODEL`, для фото — `OPENROUTER_VISION_MODEL`. По умолчанию обе используют `deepseek/deepseek-v4.1-flash-1017`. После изменения настроек перезапустите Django. [Как собирается промпт и определяется окрас](backend/docs/AI_ASSISTANT.md)

Демо-фото Барсика лежит в `backend/media/animals/demo-barsik.png`. Запрос для встроенного ImageGen:

> Фотореалистичный портрет взрослого полосатого кота Барсика. Кот сидит на светлом пледе в комнате приюта и смотрит в камеру. Мягкий дневной свет из окна, нейтральный фон, крупный план на уровне глаз, горизонтальный кадр 4:3 с запасом вокруг головы. Без надписей и водяных знаков.

## Сервер

[Как обновлять сайт через Git и systemd](deploy/README.md)
