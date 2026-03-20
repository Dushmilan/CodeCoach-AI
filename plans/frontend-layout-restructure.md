# Frontend Layout Restructure Plan

## Overview

This plan outlines the changes needed to restructure the CodeCoach-AI frontend layout to have three independent scrollable columns with specific content organization.

## User Preferences

- **Toggle Button:** Single button to switch between "Show All Questions" and "Show Active Question"
- **Output Panel:** Resizable and collapsible
- **Question Description Panel:** Examples shown by default, hints collapsible

## Current Layout Structure

```
┌────────────────────────────────────────────────────────────────────┐
│                           Header                                    │
├─────────────┬───────────────────────────────────┬─────────────────┤
│             │                                   │                 │
│  Sidebar    │   Question Article                │   AI Chat       │
│  (Problems) │   + Code Editor                   │   Panel         │
│             │   + Output Panel                  │   (w-96)        │
│  (w-80)     │                                   │                 │
│             │   (QuestionContentSection)        │                 │
│             │                                   │                 │
└─────────────┴───────────────────────────────────┴─────────────────┘
```

### Current Issues
1. No independent scrollbars for each column
2. Question description is in the center panel, not left side
3. AI Chat panel needs explicit scrollbar
4. Questions panel needs toggle between all questions and active question description

## Proposed Layout Structure

```
┌────────────────────────────────────────────────────────────────────┐
│                           Header                                    │
├─────────────┬───────────────────────────────────┬─────────────────┤
│             │ ╔═════════════════════════════╗   │                 │
│  Sidebar    │ ║   Code Editor               ║   │   AI Chat       │
│  (Problems) │ ║   (Monaco Editor)           ║   │   Panel         │
│             │ ╠═════════════════════════════╣   │   (w-96)        │
│  Toggle ──► │ ║   Output Panel              ║   │                 │
│  [Show All] │ ║   (Test Results)            ║   │   [Scrollbar]   │
│             │ ╚═════════════════════════════╝   │                 │
│  OR        │                                   │                 │
│             │                                   │                 │
│  Question   │                                   │                 │
│  Description│                                   │                 │
│             │                                   │                 │
│  [Scrollbar]│         [Scrollbar]               │                 │
└─────────────┴───────────────────────────────────┴─────────────────┘
```

## Detailed Changes

### 1. ContentLayoutContainer.tsx
**File:** [`ContentLayoutContainer.tsx`](frontend/src/components/layout/elements/ContentLayoutContainer.tsx)

**Current:**
```tsx
<div className="flex-1 flex overflow-hidden">
  {children}
</div>
```

**Proposed:**
- No structural changes needed here
- The three-column layout will be managed by the parent component

### 2. New QuestionDescriptionPanel Component
**New File:** `frontend/src/components/layout/elements/QuestionDescriptionPanel.tsx`

**Purpose:** Display the active question's description with examples in the left panel

**Props:**
- `selectedQuestion: Question`
- `difficultyBadge: string`
- `questionSummary: string | null`

**Features:**
- Scrollable content area with `overflow-y-auto`
- Question title, difficulty, and description
- **Examples section** - Shown by default, not collapsible
- **Hints section** - Collapsible (collapsed by default)
- Independent scrollbar for this panel

**Proposed Structure:**
```tsx
<div className="flex flex-col h-full overflow-hidden">
  {/* Header with toggle button */}
  <div className="p-4 border-b border-border">
    <button
      onClick={onToggleView}
      className="flex items-center gap-2 text-sm font-medium"
    >
      <List className="h-4 w-4" />
      Show All Questions
    </button>
  </div>
  
  {/* Scrollable content */}
  <div className="flex-1 overflow-y-auto p-4">
    {/* Question Header */}
    <div className="mb-4">
      <h2 className="text-xl font-semibold">{selectedQuestion.title}</h2>
      <span className={difficultyBadge}>{selectedQuestion.difficulty}</span>
      <span className="text-muted-foreground">{selectedQuestion.category}</span>
    </div>
    
    {/* Description */}
    <div className="prose prose-sm dark:prose-invert mb-4">
      <p>{selectedQuestion.description}</p>
    </div>
    
    {/* Examples - Always visible */}
    {selectedQuestion.examples?.map((example, idx) => (
      <div key={idx} className="mb-4 p-3 bg-secondary rounded-lg">
        <strong>Example {idx + 1}:</strong>
        <pre>Input: {example.input}</pre>
        <pre>Output: {example.output}</pre>
      </div>
    ))}
    
    {/* Hints - Collapsible */}
    <Collapsible defaultOpen={false}>
      <CollapsibleTrigger>
        <ChevronRight className="h-4 w-4" />
        Hints
      </CollapsibleTrigger>
      <CollapsibleContent>
        {selectedQuestion.hints?.map((hint, idx) => (
          <p key={idx}>{hint}</p>
        ))}
      </CollapsibleContent>
    </Collapsible>
  </div>
</div>
```

### 3. EnhancedSidebar.tsx Modifications
**File:** [`EnhancedSidebar.tsx`](frontend/src/components/layout/EnhancedSidebar.tsx)

**Changes:**
- Add a **single toggle button** to switch between:
  - **"Show All Questions"** - displays the full question list
  - **"Show Active Question"** - displays the selected question's description
- State management for toggle: `const [viewMode, setViewMode] = useState<'list' | 'description'>('list')`
- When in 'description' mode, render `QuestionDescriptionPanel` content
- Ensure scrollbar works independently for both modes

**Toggle Button Implementation:**
```tsx
{/* Toggle Button - Single button that switches view */}
<div className="p-3 border-b border-border">
  <button
    onClick={() => setViewMode(viewMode === 'list' ? 'description' : 'list')}
    className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
  >
    {viewMode === 'list' ? (
      <>
        <FileText className="h-4 w-4" />
        Show Active Question
      </>
    ) : (
      <>
        <List className="h-4 w-4" />
        Show All Questions
      </>
    )}
  </button>
</div>

{/* Content Area with Independent Scrollbar */}
<div className="flex-1 overflow-y-auto">
  {viewMode === 'list' ? (
    {/* Questions List */}
  ) : (
    <QuestionDescriptionPanel
      selectedQuestion={selectedQuestion}
      difficultyBadge={difficultyBadge}
      questionSummary={questionSummary}
    />
  )}
</div>
```

### 4. CodeEditorContainer.tsx Modifications
**File:** [`CodeEditorContainer.tsx`](frontend/src/components/layout/elements/CodeEditorContainer.tsx)

**Changes:**
- Split into two sections:
  1. **Code Editor Section** - Monaco editor (flexible height)
  2. **Output Panel Section** - Test results/output (resizable and collapsible)
- Add resize handle between editor and output
- Add collapse/expand button for output panel
- Use flex-col with proper overflow handling

**Proposed Structure:**
```tsx
<div className="flex-1 flex flex-col overflow-hidden">
  {/* Code Editor Section */}
  <div
    className="flex-1 min-h-0 overflow-hidden"
    style={{ height: outputCollapsed ? '100%' : `calc(100% - ${outputHeight}px)` }}
  >
    <CodeEditor ... />
  </div>
  
  {/* Resize Handle (when not collapsed) */}
  {!outputCollapsed && (
    <div
      className="h-1 bg-border cursor-row-resize hover:bg-primary"
      onMouseDown={handleResizeStart}
    />
  )}
  
  {/* Output Panel Section (collapsible) */}
  {!outputCollapsed && (
    <div
      className="border-t overflow-auto"
      style={{ height: `${outputHeight}px` }}
    >
      {/* Collapse button */}
      <button onClick={() => setOutputCollapsed(true)}>
        <ChevronDown />
      </button>
      {/* Output content */}
    </div>
  )}
  
  {/* Expand button (when collapsed) */}
  {outputCollapsed && (
    <button onClick={() => setOutputCollapsed(false)}>
      <ChevronUp /> Show Output
    </button>
  )}
</div>
```

**State Management:**
```tsx
const [outputHeight, setOutputHeight] = useState(200); // Default 200px
const [outputCollapsed, setOutputCollapsed] = useState(false);
const [isResizing, setIsResizing] = useState(false);
```

### 5. AIChatPanelContainer.tsx Modifications
**File:** [`AIChatPanelContainer.tsx`](frontend/src/components/layout/elements/AIChatPanelContainer.tsx)

**Changes:**
- Add explicit overflow handling
- Ensure the container has `overflow-hidden` and the inner content has `overflow-y-auto`

### 6. AIChatPanel.tsx Modifications
**File:** [`AIChatPanel.tsx`](frontend/src/components/chat/AIChatPanel.tsx)

**Current State:**
- Line 65: `<div className="flex-1 overflow-y-auto p-4 space-y-4">` - Already has scrollbar

**Changes:**
- Verify scrollbar behavior is correct
- Ensure proper height constraints

### 7. Layout.tsx Modifications
**File:** [`Layout.tsx`](frontend/src/components/layout/Layout.tsx)

**Changes:**
- Remove `QuestionArticle` from `QuestionContentSection`
- Pass question description props to `SidebarContainer` instead
- Update the layout structure:

```tsx
<MainLayoutContainer>
  <SidebarContainer
    questions={questions}
    selectedQuestion={selectedQuestion}
    onSelectQuestion={handleQuestionSelection}
    userProgress={userProgress}
    difficultyBadge={difficultyBadge}
    questionSummary={questionSummary}
  />
  
  <MainContentContainer>
    <Header />
    <ContentLayoutContainer>
      <QuestionContentSection>
        {/* Only CodeEditorContainer now */}
        <CodeEditorContainer ... />
      </QuestionContentSection>
      <AIChatPanelContainer ... />
    </ContentLayoutContainer>
  </MainContentContainer>
</MainLayoutContainer>
```

## Component Hierarchy After Changes

```
Layout
├── MainLayoutContainer
│   ├── SidebarContainer (EnhancedSidebar)
│   │   ├── Toggle Button (Show All / Show Active)
│   │   ├── Question List (when toggle = 'list')
│   │   │   └── [Scrollbar]
│   │   └── Question Description Panel (when toggle = 'description')
│   │       └── [Scrollbar]
│   │
│   └── MainContentContainer
│       ├── Header
│       └── ContentLayoutContainer
│           ├── QuestionContentSection
│           │   ├── Code Editor (Monaco)
│           │   └── Output Panel
│           │       └── [Scrollbar]
│           │
│           └── AIChatPanelContainer
│               └── AIChatPanel
│                   └── [Scrollbar]
```

## CSS Classes for Scrollbars

Each scrollable column should have:
```css
.overflow-hidden      /* Parent container */
.flex.flex-col        /* Flex column layout */
.h-full               /* Full height */

/* Inner scrollable content */
.overflow-y-auto      /* Vertical scrollbar */
.flex-1               /* Take remaining space */
```

## Implementation Order

1. **Step 1:** Modify `EnhancedSidebar.tsx` to add toggle functionality
2. **Step 2:** Create `QuestionDescriptionPanel.tsx` component
3. **Step 3:** Update `SidebarContainer.tsx` to pass new props
4. **Step 4:** Modify `CodeEditorContainer.tsx` to separate editor and output
5. **Step 5:** Update `AIChatPanelContainer.tsx` for proper scrollbar
6. **Step 6:** Update `Layout.tsx` to remove QuestionArticle from center
7. **Step 7:** Update `QuestionContentSection.tsx` for proper overflow
8. **Step 8:** Test all scrollbars work independently

## Files to Modify

| File | Changes |
|------|---------|
| [`Layout.tsx`](frontend/src/components/layout/Layout.tsx) | Remove QuestionArticle, pass props to sidebar |
| [`EnhancedSidebar.tsx`](frontend/src/components/layout/EnhancedSidebar.tsx) | Add toggle, integrate QuestionDescriptionPanel |
| [`SidebarContainer.tsx`](frontend/src/components/layout/elements/SidebarContainer.tsx) | Pass additional props |
| [`CodeEditorContainer.tsx`](frontend/src/components/layout/elements/CodeEditorContainer.tsx) | Split editor and output |
| [`AIChatPanelContainer.tsx`](frontend/src/components/layout/elements/AIChatPanelContainer.tsx) | Add overflow handling |
| [`QuestionContentSection.tsx`](frontend/src/components/layout/elements/QuestionContentSection.tsx) | Update overflow classes |

## New Files to Create

| File | Purpose |
|------|---------|
| `QuestionDescriptionPanel.tsx` | Display question description in sidebar |

## Visual Mockup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CodeCoach AI                                                    [Theme]    │
├────────────────┬──────────────────────────────────────┬─────────────────────┤
│ [Show All] [▼] │                                      │                     │
├────────────────┤  ┌─────────────────────────────────┐ │   AI Coach          │
│ ▼ Problems      │  │ def two_sum(nums, target):      │ │                     │
│                 │  │     # Your code here            │ │   [Hint] [Review]   │
│ 🟢 Two Sum ✓   │  │     pass                         │ │   [Explain] [Debug] │
│ 🟡 Add Two      │  │                                 │ │                     │
│ 🔻 Max Subarray │  │                                 │ ├─────────────────────┤
│                 │  │                                 │ │                     │
│                 │  └─────────────────────────────────┘ │   User: Can you     │
│                 │  ┌─────────────────────────────────┐ │   give me a hint?   │
│                 │  │ Output:                         │ │                     │
│                 │  │ ✅ Test Case 1: Passed          │ │   AI: Try using a   │
│                 │  │ ✅ Test Case 2: Passed          │ │   hash map...       │
│                 │  └─────────────────────────────────┘ │                     │
│                 │                                      │   [Type message...] │
├────────────────┴──────────────────────────────────────┴─────────────────────┤
│  Total: 5    Solved: 2                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

When "Show Active" is clicked:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CodeCoach AI                                                    [Theme]    │
├────────────────┬──────────────────────────────────────┬─────────────────────┤
│ [Show Active]  │                                      │                     │
├────────────────┤  ┌─────────────────────────────────┐ │   AI Coach          │
│ Two Sum        │  │ def two_sum(nums, target):      │ │                     │
│ Easy • Arrays  │  │     # Your code here            │ │   [Hint] [Review]   │
│                │  │     pass                         │ │   [Explain] [Debug] │
│ Given an array │  │                                 │ │                     │
│ of integers... │  │                                 │ ├─────────────────────┤
│                │  │                                 │ │                     │
│ Example 1:     │  └─────────────────────────────────┘ │   User: Can you     │
│ Input: [2,7]   │  ┌─────────────────────────────────┐ │   give me a hint?   │
│ Output: [0,1]  │  │ Output:                         │ │                     │
│                │  │ ✅ Test Case 1: Passed          │ │   AI: Try using a   │
│ [Hint ▼]       │  │ ✅ Test Case 2: Passed          │ │   hash map...       │
│                │  └─────────────────────────────────┘ │                     │
│                │                                      │   [Type message...] │
└────────────────┴──────────────────────────────────────┴─────────────────────┘
```

## Confirmed Requirements

Based on user feedback:
1. **Toggle Button:** Single button that switches between "Show All Questions" and "Show Active Question"
2. **Question Description Panel:** Examples shown by default, hints collapsible (collapsed by default)
3. **Output Panel:** Resizable (via drag handle) and collapsible
4. **Each column has independent scrollbar**
