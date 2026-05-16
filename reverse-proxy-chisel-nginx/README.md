# Reverse proxy: nginx + chisel

Схема использует только публичные порты сервера `4014`, `4015`, `4016`.

- `4015` — внешний HTTP-порт веб-приложения.
- `4014` — внешний WebSocket-порт.
- `4016` — служебный порт `chisel`, к нему подключается локальный ПК.

На локальном ПК порты не меняются:

- локальное веб-приложение: `127.0.0.1:8050`
- локальный WebSocket: `127.0.0.1:8765`

Итоговая маршрутизация:

```text
http://SERVER_PUBLIC_IP:4015  -> nginx -> chisel -> 127.0.0.1:8050 на локальном ПК
ws://SERVER_PUBLIC_IP:4014    -> chisel          -> 127.0.0.1:8765 на локальном ПК
```

Nginx также переписывает в HTML/JS строку `:8765` на `:4014`, чтобы браузер не пытался идти на закрытый порт `8765` белого сервера.

## 1. Запуск на сервере

```bash
cd server
cp .env.example .env
nano .env
```

Задайте пароль:

```env
CHISEL_USER=user
CHISEL_PASSWORD=your_strong_password
```

Запуск:

```bash
./start-server.sh
```

Или напрямую:

```bash
docker compose up -d
```

Проверка контейнеров:

```bash
docker compose ps
```

Остановка:

```bash
./stop-server.sh
```

## 2. Запуск клиента на локальном ПК

Сначала проверьте, что локально работают оба сервиса:

```bash
curl http://127.0.0.1:8050
```

WebSocket должен слушать на `127.0.0.1:8765`.

### Вариант A: chisel установлен локально

```bash
export SERVER_PUBLIC_IP=84.237.52.214
export CHISEL_USER=user
export CHISEL_PASSWORD=your_strong_password
./client/run-client.sh
```

Эквивалентная команда без скрипта:

```bash
chisel client \
  --auth user:your_strong_password \
  84.237.52.214:4016 \
  R:0.0.0.0:18050:127.0.0.1:8050 \
  R:0.0.0.0:4014:127.0.0.1:8765
```

### Вариант B: клиент через Docker на Linux

```bash
export SERVER_PUBLIC_IP=84.237.52.214
export CHISEL_USER=user
export CHISEL_PASSWORD=your_strong_password
./client/run-client-docker-linux.sh
```

### Вариант C: клиент через Docker Desktop на macOS/Windows

```bash
export SERVER_PUBLIC_IP=84.237.52.214
export CHISEL_USER=user
export CHISEL_PASSWORD=your_strong_password
./client/run-client-docker-desktop.sh
```

## 3. Как открывать приложение

В браузере открывайте:

```text
http://84.237.52.214:4015
```

Фронтенд должен начать ходить на:

```text
ws://84.237.52.214:4014/
```

А не на:

```text
ws://84.237.52.214:8765/
```

## 4. Диагностика

Логи nginx:

```bash
cd server
docker compose logs -f nginx
```

Логи chisel-сервера:

```bash
cd server
docker compose logs -f chisel
```

Проверить, что сервер слушает нужные порты:

```bash
ss -lntp | grep -E '4014|4015|4016'
```

Проверить HTTP с внешней машины:

```bash
curl -v http://84.237.52.214:4015
```

Проверить, что nginx реально переписывает порт в отдаваемых файлах:

```bash
curl -s http://84.237.52.214:4015 | grep -E '8765|4014'
```

Если в браузере всё ещё видно `ws://84.237.52.214:8765/`, значит порт `8765` формируется не простым текстом в HTML/JS или файл пришёл из кэша браузера. Сначала сделайте hard refresh / очистку кэша. Если не помогло, нужно точечно посмотреть файл `websocket-client.js` и добавить более конкретную подмену в `server/nginx/default.conf`.
