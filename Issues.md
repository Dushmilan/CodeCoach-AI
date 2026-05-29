
# Active Issues

1. **AI Chat Layout Collapse**: AI Chat Panel forces layout collapse to full-screen when long strings are generated, effectively hiding the code editor.
2. **Quality of Generated Test Cases**: AI-generated questions frequently fail the quality gate (0/87 pass rate) due to schema inconsistencies between the NIM generator and Pydantic validation schemas.

# Resolved Issues

1. **FIXED**: Code submission input parsing (backend). `PistonService` was passing raw strings to functions instead of parsed lists, causing `find_duplicates` to iterate characters of the input string.
2. **FIXED**: Code submission `NameError` (backend). Suite runners hardcoded `solve()` as the entry point, breaking functions named `find_duplicates` etc.
3. **FIXED**: Code submission `TypeError` (backend). Suite runners had invalid syntax (`json.dumps` over a generator) in the new batch execution refactor.
4. **FIXED**: Frontend build crash (frontend). Added missing `styled-jsx` dependency and switched from `pnpm` to `npm` in `Dockerfile`.
5. **FIXED**: Next.js pre-rendering error (frontend). Wrapped `/login` page `useSearchParams` in `Suspense`.
