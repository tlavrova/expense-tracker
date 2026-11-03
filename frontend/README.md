# Expense Tracker – frontend

Angular 22 app (standalone components, signals, zoneless). See the [main README](../README.md)
for the stages and how it connects to the backend.

```bash
npm install
npm start        # http://localhost:4200
npm test         # Vitest unit tests
npm run build    # production build in dist/
```

All data goes through `src/app/expense.service.ts`. It serves mock data for now (stage 10a);
stage 10 switches it to `HttpClient` calls to the FastAPI backend.
