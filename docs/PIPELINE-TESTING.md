# IRIS Web Pipeline Testing Guide

## Overview
This document outlines how to test local changes with the same build process used by the Jenkins CI/CD pipeline to ensure changes will be properly included in production builds.

## Jenkins Pipeline Build Process

The Jenkins pipeline builds Docker images using this command structure:
```bash
docker build --build-arg VERSION=$version --push $dockerBuildCommandTags -f ./docker/webApp/Dockerfile .
```

### Key Components:
- **Dockerfile**: `./docker/webApp/Dockerfile`
- **Build Context**: Current directory (`.`)
- **Source Copy**: Line 65 in Dockerfile: `COPY ./source .`

## Testing Local Changes

### 1. Make Your Changes
Edit files in the `source/` directory (e.g., templates, CSS, Python files).

### 2. Test with Jenkins-Style Build Command
```bash
# Build using the same command structure as Jenkins
docker build --build-arg VERSION=test -t iris-web-test -f ./docker/webApp/Dockerfile .
```

### 3. Verify Changes Are Included
```bash
# Check specific files in the built image
docker run --rm iris-web-test sh -c "cat /iriswebapp/path/to/your/file"

# Example: Check login template
docker run --rm iris-web-test sh -c "grep 'Ironclad' /iriswebapp/app/blueprints/login/templates/login.html"
```

## Docker Compose vs Jenkins Pipeline

### Docker Compose (Development)
- Uses `docker-compose.yml` configuration
- May have different caching behavior
- Command: `docker-compose up -d --build`

### Jenkins Pipeline (Production)
- Uses direct `docker build` command
- Builds from root directory with specific Dockerfile
- Includes version build arguments

## Cache Considerations

### When Docker Compose Changes Don't Appear:
1. **Stop containers**: `docker-compose down`
2. **Remove cached images**: `docker rmi iriswebapp_app:v2.4.22`
3. **Rebuild**: `docker-compose up -d --build`

### Jenkins Pipeline Cache:
- Jenkins builds use the same Docker layer caching
- Local file changes are automatically included via `COPY ./source .`
- No special cache clearing needed for file changes

## Best Practices

1. **Always test with Jenkins command structure** before pushing changes
2. **Verify critical changes** by inspecting the built image
3. **Document file paths** for easier verification
4. **Test both development and production build methods**

## Common File Paths in Container

- Templates: `/iriswebapp/app/blueprints/*/templates/`
- CSS: `/iriswebapp/app/static/assets/css/`
- Python modules: `/iriswebapp/app/`

## Troubleshooting

If changes don't appear in Jenkins builds:
1. Verify files are in the `source/` directory
2. Check file permissions and Git tracking
3. Test with local Jenkins command structure
4. Inspect built image contents