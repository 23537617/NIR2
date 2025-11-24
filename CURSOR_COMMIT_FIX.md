# Решение проблемы зависания коммита в Cursor

## Проблема
Cursor IDE зависает при попытке создать commit через GUI.

## Быстрое решение: Использование терминала

Вместо GUI в Cursor, используйте терминал:

```bash
# Проверить статус
git status

# Добавить файлы
git add <файл>
# или
git add .

# Создать коммит
git commit -m "Ваше сообщение коммита"

# Отправить на GitHub
git push
```

## Альтернативные решения

### 1. Проверка процессов Git

Cursor может зависать из-за других процессов Git:

```bash
# Windows: Проверить процессы Git
tasklist | findstr git

# Закрыть зависший процесс Git (если есть)
taskkill /F /IM git.exe
```

### 2. Перезапуск Cursor

1. Закройте Cursor полностью
2. Откройте снова
3. Попробуйте коммит снова

### 3. Отключение Git расширений в Cursor

Если установлены расширения Git:
1. Откройте Extensions (Ctrl+Shift+X)
2. Временно отключите Git-расширения
3. Попробуйте коммит через встроенный Git в Cursor

### 4. Проверка настроек Cursor

Проверьте настройки Git в Cursor:
- File → Preferences → Settings
- Поиск: "git"
- Убедитесь, что:
  - `git.enabled` = true
  - `git.autoRepositoryDetection` = true
  - `git.autofetch` = false (может замедлять)

### 5. Очистка индекса Git

Иногда помогает очистка:

```bash
# Сохранить изменения в stash
git stash

# Очистка
git gc --prune=now

# Вернуть изменения
git stash pop
```

### 6. Проверка размера репозитория

Хотя у вас маленький репозиторий, проверьте:

```bash
git count-objects -vH
```

### 7. Использование другой IDE/редактора для Git

Временно можно использовать:
- **Git Bash** (Windows)
- **GitHub Desktop**
- **SourceTree**
- **VS Code** (с Git расширением)

## Рекомендации

1. **Всегда используйте терминал для Git операций** - это быстрее и надежнее
2. **Используйте алиасы** для быстрых команд:

```bash
# Добавить в .gitconfig
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
```

3. **Коммитьте часто** - маленькие коммиты лучше больших

## Настройка терминала в Cursor

Для удобной работы с Git в терминале Cursor:

1. Откройте терминал: `` Ctrl+` ``
2. Используйте встроенный PowerShell/Bash
3. Настройте свой профиль терминала

## Проверка здоровья Git

```bash
# Проверить конфигурацию
git config --list

# Проверить репозиторий
git fsck

# Проверить размер .git папки
du -sh .git  # Linux/Mac
dir .git /s  # Windows
```

## Если ничего не помогает

1. **Обновите Cursor** до последней версии
2. **Создайте issue на GitHub** для Cursor:
   - https://github.com/getcursor/cursor/issues
   - Укажите версию Cursor, ОС, и описание проблемы
3. **Используйте командную строку** - это самый надежный способ

