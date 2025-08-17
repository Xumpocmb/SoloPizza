#!/bin/bash

# Скрипт для исправления проблем с entry_points.txt в виртуальном окружении

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Функция для поиска и исправления проблемных файлов entry_points.txt
fix_entry_points() {
    local venv_path=$1
    echo "Проверка виртуального окружения: $venv_path"
    
    if [ ! -d "$venv_path" ]; then
        echo "✗ Виртуальное окружение не найдено: $venv_path"
        return 1
    fi
    
    # Поиск всех файлов entry_points.txt в виртуальном окружении
    local entry_points_files=$(find "$venv_path" -name "entry_points.txt" 2>/dev/null)
    
    if [ -z "$entry_points_files" ]; then
        echo "✗ Файлы entry_points.txt не найдены в $venv_path"
        return 1
    fi
    
    echo "Найдены файлы entry_points.txt:"
    echo "$entry_points_files"
    echo ""
    
    # Проверка и исправление каждого файла
    for file in $entry_points_files; do
        echo "Проверка файла: $file"
        
        # Проверка на наличие некорректных символов в файле
        if grep -q -P "[^\x00-\x7F]" "$file"; then
            echo "✗ Найдены некорректные символы в файле $file"
            echo "Создание резервной копии..."
            cp "$file" "${file}.bak"
            
            echo "Исправление файла..."
            # Удаление некорректных символов и сохранение только ASCII
            tr -cd '\11\12\15\40-\176' < "${file}.bak" > "$file"
            echo "✓ Файл исправлен: $file"
        else
            echo "✓ Файл в порядке: $file"
        fi
    done
    
    return 0
}

# Проверка локального виртуального окружения
if [ -d "venv" ]; then
    echo "Проверка локального виртуального окружения..."
    fix_entry_points "$(pwd)/venv"
    local_result=$?
else
    echo "Локальное виртуальное окружение не найдено."
    local_result=1
fi

# Проверка виртуального окружения на сервере
if [ -d "/home/solopizzaadmin/SoloPizza/venv" ]; then
    echo "Проверка виртуального окружения на сервере..."
    fix_entry_points "/home/solopizzaadmin/SoloPizza/venv"
    server_result=$?
else
    echo "Виртуальное окружение на сервере не найдено."
    server_result=1
fi

echo ""
echo "Результаты проверки:"
if [ $local_result -eq 0 ] || [ $server_result -eq 0 ]; then
    echo "✓ Проверка и исправление файлов entry_points.txt завершены."
    echo "Попробуйте запустить Celery снова с помощью ./run_celery.sh"
else
    echo "✗ Не удалось найти или исправить файлы entry_points.txt."
    echo "Рекомендуется переустановить Celery и его зависимости:"
    echo "pip install --upgrade celery django-celery-beat django-celery-results"
fi