## Problem

The theme toggle text in the header causes a React hydration mismatch:

```
Text content did not match. Server: "Dark Mode" Client: "Light Mode"
Error: There was an error while hydrating this Suspense boundary. Switched to client rendering.
```

## Root Cause

In `frontend/src/components/header/Header.tsx:202`, the theme toggle text reads:

```tsx
{
  resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
}
```

During SSR, `resolvedTheme` is `undefined` (next-themes resolves client-side only), so `undefined === 'dark'` is `false` -- server renders "Dark Mode". After hydration, the client resolves the actual theme preference and renders differently.

The icon on lines 86-94 already has a `mounted` guard to prevent this exact class of bug, but the text was unprotected.

## Fix

Wrap the toggle text in the same `mounted` guard:

```tsx
{
  mounted ? (resolvedTheme === 'dark' ? 'Light Mode' : 'Dark Mode') : 'Theme';
}
```

Also fixes 2 pre-existing test failures in `Header.test.tsx` -- the tests used `getByTestId("sun-icon")` / `getByTestId("moon-icon")` which targeted a dead `@/components/ui/icons` mock (Header imports from lucide-react directly). Replaced with `findByText` assertions that test the actual toggle text.
