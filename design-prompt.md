# CodeCoach AI — Design Prompt for OpenDesign

## Product
CodeCoach AI is an open-source LeetCode alternative for university students. Users practice coding interview questions with instant feedback, AI coaching, and progress tracking — powered by NVIDIA's free-tier LLaMA API.

## Target Audience
University students (18–25) preparing for technical interviews at big tech companies. They are comfortable with dark-mode UIs, use platforms like VS Code, LeetCode, and Replit daily.

## Vibe & Visual Direction
- **Vibe:** Modern, professional, approachable — like VS Code + Linear + LeetCode had a baby
- **Dark-first:** Dark mode default (light mode secondary). Deep navy/charcoal backgrounds.
- **Accent color:** Electric blue primary (#3B82F6 range) with subtle purple/indigo gradients for AI-related elements
- **Typography:** Inter font, clean hierarchy
- **Feel:** Fast, responsive, code-native. Minimal chrome, maximum content area.
- **Tone:** Encouraging and smart — not corporate, not childish

## Pages / Screens to Design

### 1. Home / Workspace (the main screen)
The user spends 90% of their time here. Layout:
- **Left sidebar:** Question list with search/filter (difficulty, category, company tags)
- **Center top:** Question description / prompt (collapsible)
- **Center main:** Monaco code editor (largest surface area)
- **Right panel:** AI coach chat panel (collapsible) — shows streaming AI responses
- **Top header:** Logo, settings gear, user avatar, theme toggle

### 2. Question Browser
A nice grid or list view of all questions with:
- Filter chips (Easy/Medium/Hard, categories, companies)
- Search bar
- Each card shows: title, difficulty badge, category tags, completion rate

### 3. Landing / Marketing Page
- Hero section with animated code editor mockup
- Features grid (AI coaching, multi-language, progress tracking)
- "Start coding free" CTA
- Footer with GitHub link

### 4. Auth Pages
- Login / Sign up (Supabase magic link or email/password)
- Clean, minimal, centered card layout

## Existing Design Tokens (keep or evolve)
- Uses shadcn/ui CSS variable pattern in `globals.css`
- Current dark theme: deep navy background (222.2 84% 4.9%), blue primary (217.2 91.2% 59.8%)
- Radix UI primitives for dropdowns, etc.
- Lucide icons
- Tailwind CSS 3

## Constraints
- Must remain Tailwind CSS + CSS variables (no styled-components or CSS-in-JS)
- Must keep Monaco editor accessible
- Responsive down to 1024px (not mobile-first — this is a desktop app)
- Animations should be subtle and purposeful (no gratuitous motion)

## Deliverables
For each screen:
1. A clear visual direction
2. Color palette refinements (if any)
3. Component hierarchy
4. Layout specs (grid, spacing, responsive breakpoints)

## References for Inspiration
- Linear.app (clean dark UI, typography)
- LeetCode (problem layout, editor integration)
- VS Code (sidebar patterns, color theming)
- Claude.ai (AI chat panel design)
