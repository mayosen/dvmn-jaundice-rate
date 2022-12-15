# Фильтр желтушных новостей

[TODO. Опишите проект, схему работы]

Пока поддерживается только один новостной сайт - [ИНОСМИ.РУ](https://inosmi.ru/). 
Для него разработан специальный адаптер, умеющий выделять текст статьи на фоне остальной HTML разметки.
Для других новостных сайтов потребуются новые адаптеры, все они будут находиться в каталоге `adapters`. 
Туда же помещен код для сайта ИНОСМИ.РУ: `adapters/inosmi_ru.py`.

В перспективе можно создать универсальный адаптер, подходящий для всех сайтов, но его разработка будет сложной 
и потребует дополнительных времени и сил.

# Как установить

Вам понадобится Python версии 3.7 или старше. Для установки пакетов рекомендуется создать виртуальное окружение.

Первым шагом установите пакеты:

```bash
$ pip install -r requirements.txt
```

# Как запустить

```bash
$ python jaundice_rate/analyzer.py
```

# Как запустить тесты

Для тестирования используется [pytest](https://docs.pytest.org/en/latest/).
Тестами покрыты фрагменты кода, сложные в отладке: `text_tools.py` и адаптеры. 

Команда для запуска тестов:
```bash
$ python -m pytest
```

# Цели проекта

Код написан в учебных целях. Это урок из курса по веб-разработке — [Девман](https://dvmn.org).
