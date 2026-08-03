'use client';

import { useMemo } from 'react';
import DOMPurify from 'dompurify';

interface MarkdownRendererProps {
  content: string;
}

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Sanitize generated HTML with DOMPurify.
 *
 * The markdown renderer escapes all user content, so only controlled tags
 * (headings, paragraphs, code, strong, li) reach here. DOMPurify is applied
 * as a robust, battle-tested final defense in depth instead of hand-rolled
 * regexes (which are bypass-prone).
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['h1', 'h2', 'h3', 'p', 'li', 'pre', 'code', 'strong', 'em', 'br'],
    ALLOWED_ATTR: ['class'],
  });
}

export function renderMarkdown(md: string): string {
  const lines = md.split('\n');
  const html: string[] = [];
  let inCodeBlock = false;
  let codeBuffer: string[] = [];
  let codeLang = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('```')) {
      if (inCodeBlock) {
        html.push(
          `<pre><code class="language-${escapeHtml(codeLang)}">${escapeHtml(codeBuffer.join('\n'))}</code></pre>`,
        );
        codeBuffer = [];
        codeLang = '';
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
        codeLang = line.slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    if (line.startsWith('### ')) {
      html.push(
        `<h3 class="text-lg font-semibold mt-6 mb-2 text-foreground/90">${escapeHtml(line.slice(4))}</h3>`,
      );
    } else if (line.startsWith('## ')) {
      html.push(
        `<h2 class="text-xl font-semibold mt-8 mb-3 text-foreground/90">${escapeHtml(line.slice(3))}</h2>`,
      );
    } else if (line.startsWith('# ')) {
      html.push(
        `<h1 class="text-2xl font-semibold mt-8 mb-4 text-foreground/90">${escapeHtml(line.slice(2))}</h1>`,
      );
    } else if (line.startsWith('- ')) {
      html.push(`<li class="ml-4 text-foreground/80">${escapeHtml(line.slice(2))}</li>`);
    } else if (line.startsWith('**') && line.endsWith('**')) {
      html.push(
        `<p class="font-semibold text-foreground/80 mt-3">${escapeHtml(line.slice(2, -2))}</p>`,
      );
    } else if (line.trim() === '') {
      if (html.length > 0 && !html[html.length - 1].startsWith('<li')) {
        html.push('<br/>');
      }
    } else {
      const processed = escapeHtml(line)
        .replace(
          /`([^`]+)`/g,
          '<code class="bg-white/5 px-1.5 py-0.5 rounded text-sm font-mono text-primary/80">$1</code>',
        )
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html.push(`<p class="text-foreground/80 leading-relaxed">${processed}</p>`);
    }
  }

  if (inCodeBlock && codeBuffer.length > 0) {
    html.push(`<pre><code>${escapeHtml(codeBuffer.join('\n'))}</code></pre>`);
  }

  return html.join('\n');
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const html = useMemo(() => sanitizeHtml(renderMarkdown(content)), [content]);

  return (
    <div
      className="prose prose-sm max-w-none text-foreground/80"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
