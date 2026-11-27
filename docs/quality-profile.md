# Профиль качества проекта (ЛР-8)

## 1. Статический анализ (SonarCloud)
По результатам первого прогона анализатора:
- **Lines of Code:** 374
- **Security Issues:** 9 (Rating D)
- **Reliability Issues:** 10 (Rating C)
- **Maintainability Issues:** 0 (Rating A)
- **Duplications:** 0.0%

## 2. Покрытие тестами
- **Покрытие:** 86% (по данным CI-конвейера `pytest-cov` из ЛР-7).
- **Порог:** 60% (зафиксирован в `.github/workflows/ci.yml`).
- *Примечание:* Мы используем данные из нашего CI-конвейера.
