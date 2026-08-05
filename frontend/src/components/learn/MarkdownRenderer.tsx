"use client";

import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
}

const COMPONENTS: Components = {
  h1: ({ children }) => (
    <h1 className="text-2xl font-semibold mt-8 mb-4 text-foreground/90">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-xl font-semibold mt-8 mb-3 text-foreground/90">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-lg font-semibold mt-6 mb-2 text-foreground/90">
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-base font-semibold mt-5 mb-2 text-foreground/90">
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p className="text-foreground/80 leading-relaxed my-3">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-6 my-3 space-y-1.5 text-foreground/80">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-6 my-3 space-y-1.5 text-foreground/80">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  code: ({ className, children }) =>
    className || String(children).includes("\n") ? (
      <code className={className}>{children}</code>
    ) : (
      <code className="bg-white/5 px-1.5 py-0.5 rounded text-sm font-mono text-primary/80">
        {children}
      </code>
    ),
  pre: ({ children }) => (
    <pre className="bg-black/40 border border-white/10 rounded-lg p-4 overflow-x-auto text-sm font-mono my-4">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="overflow-x-auto my-4">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-white/[0.04]">{children}</thead>
  ),
  th: ({ children }) => (
    <th className="border border-white/10 px-3 py-2 text-left font-semibold text-foreground/90">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-white/10 px-3 py-2 text-foreground/80 align-top">
      {children}
    </td>
  ),
  a: ({ href, children }) => {
    if (!href || !/^(https?:|mailto:|\/|#)/i.test(href)) {
      return <span className="text-foreground/80">{children}</span>;
    }
    const external = href.startsWith("http");
    return (
      <a
        href={href}
        className="text-primary/80 underline underline-offset-2 hover:text-primary"
        target={external ? "_blank" : undefined}
        rel={external ? "noreferrer" : undefined}
      >
        {children}
      </a>
    );
  },
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-primary/40 pl-4 my-3 text-foreground/70 italic">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-6 border-white/10" />,
  strong: ({ children }) => (
    <strong className="font-semibold text-foreground/90">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-foreground/80">{children}</em>
  ),
};

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={COMPONENTS}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
