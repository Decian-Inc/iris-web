# CLAUDE.md - Development Guide for IRIS

## Project Overview
IRIS (Incident Response Investigation System) is a web collaborative platform for incident responders. Version: v2.4.22

## Architecture
- **Flask-based web application** with PostgreSQL database
- **Docker containerized** with 5 services: app, db, rabbitmq, worker, nginx
- **Modular design** with IrisWeb core and IrisModules extensions

## SOAR Integrations

- **All soar integration standards, practices, and codestyles, are located in SOAR-integration-format-style.md**

## Development Workflow

### Branching Strategy
- Main development on `develop` branch
- Small/safe changes directly on `develop`
- Larger/risky changes on feature branches
- PRs target `develop` (not `master`)
- Production releases tagged from `master`

### Commit Convention
- Format: `[action] Commit message` or `[#issue_id][action] Commit message`
- Actions: `ADD`, `DEL`, `IMP`, `FIX`, etc.

## Code Structure

### Backend (Python/Flask)
- **Routes**: `source/app/blueprints/` - organized by UI menu categories
- **Database**: `source/app/datamgmt/` - separated from routes
- **Templates**: `source/app/templates/` and route-specific template dirs
- **Static assets**: `source/app/static/assets/`

### Python Standards
- No shebangs in files
- Use f-strings for string interpolation
- Prefix private members with underscore (`_`)
- New files need LGPL license header (see CODESTYLE.md)

### JavaScript Standards
- Use `===` instead of `==`
- Use `!==` instead of `!=`
- Use template literals instead of string concatenation

### Database Changes
- Create Alembic migrations: `alembic -c app/alembic.ini revision -m "Description"`
- Modify scripts in `source/app/alembic/`

## Development Environment

### Docker Setup
```bash
# Development build (local images)
docker-compose up --build

# Production setup
docker-compose -f docker-compose.yml up
```

### Services
- **app**: Core web server (port 8000)
- **db**: PostgreSQL database (port 5432)
- **rabbitmq**: Message queue
- **worker**: Background job processor
- **nginx**: Reverse proxy (HTTPS on 443)

## Testing & Quality
- Test files in `tests/` directory
- Follow project's testing patterns
- Run linting/typecheck commands before commits

## Key Directories
- `source/app/blueprints/` - Route definitions
- `source/app/datamgmt/` - Database operations
- `source/app/templates/` - HTML templates
- `source/app/static/assets/` - CSS, JS, images
- `source/app/alembic/` - Database migrations
- `docker/` - Docker build contexts

## Documentation
- Main docs: https://docs.dfir-iris.org
- API reference: https://docs.dfir-iris.org/operations/api/
- Development guide: https://docs.dfir-iris.org/development/

## License
LGPL v3 - Include license header in new files (see CODESTYLE.md)