# Frontend UI стенда

Демонстрационный UI для стенда агентного анализа телеметрии КА.

## Что реализовано

- Двухколоночный layout:
  - слева: состояние КА, схема подсистем, орбитальный контекст, телеметрия;
  - справа: граф работы агента, рассуждения, вызовы инструментов, план УВ, проверка плана.
- Селектор сценариев НС: `MIXED / THERMAL / POWER / ADCS / RF / NOMINAL`.
- Граф выполнения в визуальном стиле LangGraph Studio:
  - ветвление `classification -> deep_research` или `classification -> nominal_summary`;
  - подсветка `running/done/pending/skip`.
- Масштаб графа агента колесиком мыши в окне графа.
- Кликабельные узлы графа + панель деталей по узлу.
- Интерактивные графики ТМИ:
  - ползунок `начало окна`;
  - ползунок `размер окна`;
  - подсказки по точкам при наведении.
- Режим дашборда для окон:
  - перетаскивание карточек за заголовок;
  - изменение размеров карточек мышью за края и углы;
  - привязка к сетке (snap-to-grid);
  - авто-пересборка соседних окон без наложений.
- Кнопка `Стандартная раскладка` для возврата к базовому расположению окон.
- Орбитальный контекст и подписи на русском.
- Отрисовка 2D-орбиты вокруг Земли (mock или API).
- Режим по умолчанию: `mock` (без backend).
- Опциональный режим `backend`: UI пытается вызвать:
  - `GET /health`
  - `POST /api/v1/analyze/envelope`
  - `POST /api/v1/envelope/enrich`
  - `POST /api/v1/telemetry/window`
  - `POST /api/v1/orbit/track`

## Запуск

Через общий compose:

```bash
cd /Users/litvan/space_agent
docker compose up --build
```

Открыть UI:

- `http://localhost:8080`

Backend API (если поднят):

- `http://localhost:8000/docs`

## Файлы

- `/Users/litvan/space_agent/frontend/index.html`
- `/Users/litvan/space_agent/frontend/styles.css`
- `/Users/litvan/space_agent/frontend/app.js`
