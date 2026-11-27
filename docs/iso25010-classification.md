# Классификация замечаний по ISO 25010

| № | Замечание (SonarCloud) | Файл | Характеристика ISO 25010 | Влияние |
|---|---|---|---|---|
| 1 | Make sure disabling CSRF protection is safe here | app.py | Безопасность (Security) | Высокое. Уязвимость к CSRF-атакам |
| 2 | Omitting "--only-binary :all:" can lead to execution... | ci.yml | Безопасность (Security) | Среднее. Риск атаки на цепочку поставок |
| 3 | Using dependencies without locking resolved versions... | ci.yml | Безопасность (Security) | Среднее. Непредсказуемые обновления |
| 4 | Add an "id" attribute to this input field... | booking.html | Надёжность (Reliability) / Доступность | Низкое. Проблемы с доступностью (a11y) |
| 5 | Add an "id" attribute to this input field... | catalog.html | Надёжность (Reliability) / Доступность | Низкое. Проблемы с доступностью (a11y) |
| 6 | Add an "id" attribute to this input field... | hall.html | Надёжность (Reliability) / Доступность | Низкое. Проблемы с доступностью (a11y) |
| 7 | Omitting "--only-binary :all:" can lead to execution... | ci.yml (L24) | Безопасность (Security) | Среднее. Риск атаки |
| 8 | Using dependencies without locking resolved versions... | ci.yml (L24) | Безопасность (Security) | Среднее. Непредсказуемые обновления |
| 9 | Omitting "--only-binary :all:" can lead to execution... | ci.yml (L25) | Безопасность (Security) | Среднее. Риск атаки |
| 10 | Using dependencies without locking resolved versions... | ci.yml (L26) | Безопасность (Security) | Среднее. Непредсказуемые обновления |
