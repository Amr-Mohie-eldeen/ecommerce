Local development configuration lives here.

- `docker-compose.yml`: Core dependencies for running services locally.
- `configs/`: Optional service-specific config files.

Usage:

```
make local-up
make create-topics
make local-health
make seed-data
make local-down
```

Services
- Catalog API: http://localhost:8001
- Orders API: http://localhost:8002
- Recommender: http://localhost:8003

Notes
- Compose loads env from repo `.env` and app `.env.example` files.
- Build the app images on first run; ensure internet access for Docker to install Python deps.
