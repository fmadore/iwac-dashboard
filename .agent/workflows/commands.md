---
description: Run development, build, check, and test commands
---

# Common Commands

// turbo-all

## Development

Start the dev server:
```bash
npm run dev
```

Open in browser automatically:
```bash
npm run dev -- --open
```

## Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

## Type Check & Lint

Type check:
```bash
npm run check
```

Lint (ESLint + Prettier):
```bash
npm run lint
```

Format code:
```bash
npm run format
```

## Testing

Unit tests (Vitest):
```bash
npm run test:unit -- --run
```

E2E tests (Playwright):
```bash
npm run test:e2e
```

All tests:
```bash
npm test
```
