# Решение проблем с медленным Git Push

## Диагностика проблемы

### 1. Проверка размера репозитория

```bash
# Размер текущего репозитория
git count-objects -vH

# Размер последнего коммита
git diff --stat HEAD~1 HEAD

# Размер всех файлов в репозитории
git ls-files | xargs du -ch | tail -1
```

### 2. Проверка скорости подключения

```bash
# Проверка ping до GitHub
ping github.com

# Проверка скорости соединения
curl -o /dev/null -s -w "Download speed: %{speed_download} bytes/sec\n" https://github.com
```

### 3. Проверка конфигурации Git

```bash
# Текущие настройки
git config --list | grep -E "(http|url|protocol)"

# Размер буфера для HTTP
git config http.postBuffer

# Таймауты
git config http.lowSpeedLimit
git config http.lowSpeedTime
```

## Возможные решения

### Решение 1: Увеличение буфера HTTP

```bash
git config --global http.postBuffer 524288000  # 500 MB
```

### Решение 2: Настройка таймаутов

```bash
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```

### Решение 3: Использование SSH вместо HTTPS

Если используете HTTPS, попробуйте SSH:

```bash
# Проверить текущий remote
git remote -v

# Изменить на SSH
git remote set-url origin git@github.com:username/repository.git
```

### Решение 4: Использование compression

```bash
# Включить компрессию (уже включено по умолчанию)
git config --global core.compression 9

# Или отключить, если это замедляет
git config --global core.compression 0
```

### Решение 5: Пакетная загрузка

```bash
# Увеличить размер пакетной загрузки
git config --global pack.windowMemory "256m"
git config --global pack.packSizeLimit "2g"
```

### Решение 6: Использование IPv4 (если проблемы с IPv6)

```bash
# Принудительно использовать IPv4
git config --global url."https://github.com/".insteadOf git@github.com:
```

Или изменить hosts файл (Windows: `C:\Windows\System32\drivers\etc\hosts`):

```
140.82.112.4 github.com
```

### Решение 7: Проверка больших файлов

```bash
# Найти большие файлы в истории
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | \
  sort --numeric-sort --key=2 | \
  tail -20

# Проверить, что не коммитим случайно большие файлы
git ls-files -z | xargs -0 du -h | sort -rh | head -20
```

### Решение 8: Очистка репозитория

```bash
# Очистка ненужных файлов
git gc --prune=now --aggressive

# Очистка reflog (если не нужен)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Решение 9: Использование прокси (если за корпоративным firewall)

```bash
# Установить прокси
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080

# Или SOCKS5
git config --global http.proxy socks5://127.0.0.1:1080
```

### Решение 10: Проверка VPN/DNS

Если используете VPN:
- Попробуйте отключить VPN
- Используйте другой DNS сервер (например, 8.8.8.8 или 1.1.1.1)

## Оптимизация .gitignore

Убедитесь, что большие файлы исключены:

```gitignore
# Docker volumes
*.volumes
ipfs-data/
*.data

# Большие файлы
*.log
*.dump
*.sql
*.zip
*.tar.gz

# Сгенерированные файлы
organizations/
channel-artifacts/

# Временные файлы
*.tmp
*.temp
.cache/
```

## Мониторинг push

```bash
# Подробный вывод при push
GIT_TRACE=1 GIT_TRACE_PERFORMANCE=1 GIT_CURL_VERBOSE=1 git push

# На Windows PowerShell:
$env:GIT_TRACE=1
$env:GIT_TRACE_PERFORMANCE=1
$env:GIT_CURL_VERBOSE=1
git push
```

## Альтернативные методы

### Разделение на несколько коммитов

Вместо одного большого коммита:

```bash
git add file1.py file2.py
git commit -m "Add file1 and file2"
git push

git add file3.py
git commit -m "Add file3"
git push
```

### Использование Git LFS для больших файлов

Если нужно коммитить большие файлы:

```bash
# Установить Git LFS
git lfs install

# Отслеживать большие файлы
git lfs track "*.pdf"
git lfs track "*.zip"

git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## Проверка состояния GitHub

Если проблема не на вашей стороне:

1. Проверьте статус GitHub: https://www.githubstatus.com/
2. Попробуйте позже (пиковые часы)
3. Проверьте ограничения репозитория (для бесплатных аккаунтов)

## Контакты поддержки

Если ничего не помогает:
- GitHub Support: https://support.github.com/
- Stack Overflow: https://stackoverflow.com/questions/tagged/git

