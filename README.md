## Разработка

Настройка окружения:

```bash
uv sync --dev
uv run pre-commit install
```

Хуки прогоняются автоматически при `git commit`. Прогнать вручную на всех файлах:

```bash
uv run pre-commit run --all-files
```