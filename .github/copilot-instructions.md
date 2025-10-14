# Copilot Instructions for Sapphire Project

## Project Overview
- This is a multi-app Django project with apps: `api`, `messaging`, `ocean`, `scheduler`, and the main config in `sapphire/`.
- SQLite is used for local development (`db.sqlite3`).
- Each app follows Django conventions: models, serializers, views, urls, migrations.

## Architecture & Data Flow
- `api/` handles core business logic and user management.
- `messaging/` manages real-time communication (likely via Django Channels, see `consumers.py` and `routing.py`).
- `ocean/` and `scheduler/` provide specialized features (details in their models/views).
- `sapphire/` contains global settings, ASGI/WGI entrypoints, and URL routing.
- Cross-app communication is via Django signals, shared models, or REST API endpoints.

## Developer Workflows
- **Run server:** `python manage.py runserver`
- **Migrations:** `python manage.py makemigrations` + `python manage.py migrate`
- **Run tests:** `python manage.py test [app]`
- **Debug:** Use Django shell: `python manage.py shell`
- **Static files:** Not explicitly managed; add handling if needed.

## Patterns & Conventions
- Serializers are in each app for API data validation (`serializers.py`).
- Views are class-based or function-based, grouped by app (`views.py`).
- URL routing is modular: each app has its own `urls.py`, included in `sapphire/urls.py`.
- Migrations are tracked per app in `migrations/`.
- Real-time features use Channels (see `consumers.py`, `routing.py`).
- Custom user logic is in `api/models.py` and related migrations.

## Integration Points
- External dependencies are listed in `requirements.txt`.
- ASGI entrypoint: `sapphire/asgi.py` (for Channels/websockets).
- WSGI entrypoint: `sapphire/wsgi.py` (for standard Django).
- Database: SQLite for dev, can be swapped in `sapphire/settings.py`.

## Examples
- To add a new API endpoint: create a view in `api/views.py`, add a serializer, and register the route in `api/urls.py`.
- To add a model: define in `[app]/models.py`, run migrations.
- To extend real-time messaging: update `messaging/consumers.py` and `messaging/routing.py`.

## Key Files
- `sapphire/settings.py`: Global config
- `[app]/models.py`: Data models
- `[app]/views.py`: Business logic
- `[app]/serializers.py`: API validation
- `[app]/urls.py`: Routing
- `[app]/consumers.py`: Real-time features (if present)

---
_If any section is unclear or missing, please provide feedback to improve these instructions._
