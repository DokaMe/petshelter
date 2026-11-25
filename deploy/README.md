# Как обновлять Pet Shelter на сервере

Сайт работает на [nika.romanenko-coding.ru](https://nika.romanenko-coding.ru/). Django-админка находится по адресу [nika.romanenko-coding.ru/admin/](https://nika.romanenko-coding.ru/admin/).

## Обновление через GitHub

Сначала внесите изменения в [DokaMe/petshelter](https://github.com/DokaMe/petshelter) и добавьте их в ветку `main`. Войдите на сервер командой `ssh dasha@193.233.136.221` и перейдите в рабочую копию `cd /srv/petshelter-nika/repo`.

Для обычного обновления нужны две команды.

```sh
git pull --ff-only
sudo systemctl restart petshelter-nika.service
```

При появлении нового коммита служба собирает TypeScript, устанавливает Python-зависимости, делает резервную копию SQLite, применяет миграции и запускает Gunicorn. При повторном рестарте того же коммита она использует готовую сборку.

## Как проверить обновление

```sh
sudo systemctl status petshelter-nika.service --no-pager
sudo journalctl -u petshelter-nika.service -n 80 --no-pager
curl -fsS https://nika.romanenko-coding.ru/revision.txt
```

Откройте каталог и убедитесь, что фото загружаются. Войдите, откройте «Мои подопечные» и обновите страницу, чтобы проверить восстановление входа.

## Данные, настройки и файлы

| Назначение | Путь |
| --- | --- |
| Git-репозиторий | `/srv/petshelter-nika/repo` |
| Текущая сборка | `/srv/petshelter-nika/current` |
| SQLite | `/srv/petshelter-nika/shared/db.sqlite3` |
| Загруженные фотографии | `/srv/petshelter-nika/shared/media` |
| Резервные копии перед миграцией | `/srv/petshelter-nika/shared/backups` |
| Актуальная статика | `/srv/petshelter-nika/current/frontend/dist/static` |
| Закрытый файл переменных окружения | `/etc/petshelter-nika.env` |
| systemd unit | `/etc/systemd/system/petshelter-nika.service` |
| Конфигурация сайта в Nginx | `/etc/nginx/sites-available/petshelter-nika` |

Для изменения каталога и загрузки фото используйте Django-админку. Для изменений интерфейса правьте `frontend/src/`, для изменений API — приложения в `backend/`. Настройки OpenRouter и Битрикс24 меняются в закрытом файле окружения. После изменения переменных перезапустите службу.

## Изменение инфраструктуры и откат

Если менялся unit, после `git pull` обновите установленную копию и перезапустите службу.

```sh
sudo install -m 0644 deploy/systemd/petshelter-nika.service /etc/systemd/system/petshelter-nika.service
sudo systemctl daemon-reload
sudo systemctl restart petshelter-nika.service
```

Если менялся конфиг Nginx, установите его, проверьте синтаксис и только потом перечитайте конфигурацию.

```sh
sudo install -m 0644 deploy/nginx/petshelter-nika.conf /etc/nginx/sites-available/petshelter-nika
sudo nginx -t
sudo systemctl reload nginx
```

Для отката кода сделайте `git revert` проблемного коммита в GitHub и повторите обычное обновление. Если релиз менял схему базы, проверьте совместимость миграций с предыдущим кодом. Резервную копию выбирайте по времени релиза и восстанавливайте с остановленной службой. Восстановление SQLite вернёт данные к моменту создания копии.

Сертификат выпущен Certbot с webroot. Задача `certbot.timer` проверяет срок автоматически, а deploy-hook перечитывает Nginx после обновления сертификата. [Справка Certbot](https://eff-certbot.readthedocs.io/en/stable/using.html#webroot)
