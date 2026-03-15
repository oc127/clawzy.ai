import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

const components: Components = {
  code({ className, children, ...props }) {
    const isBlock = className?.includes("language-");
    if (isBlock) {
      return (
        <pre className="my-2 overflow-x-auto rounded-xl bg-muted p-4">
          <code className={`font-mono text-sm ${className ?? ""}`} {...props}>
            {children}
          </code>
        </pre>
      );
    }
    return (
      <code
        className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre({ children }) {
    return <>{children}</>;
  },
  a({ children, ...props }) {
    return (
      <a className="text-primary hover:underline" target="_blank" rel="noopener noreferrer" {...props}>
        {children}
      </a>
    );
  },
  ul({ children }) {
    return <ul className="my-1 ml-4 list-disc space-y-0.5">{children}</ul>;
  },
  ol({ children }) {
    return <ol className="my-1 ml-4 list-decimal space-y-0.5">{children}</ol>;
  },
  p({ children }) {
    return <p className="my-1">{children}</p>;
  },
  strong({ children }) {
    return <strong className="font-semibold">{children}</strong>;
  },
  table({ children }) {
    return (
      <div className="my-2 overflow-x-auto">
        <table className="w-full border-collapse text-sm">{children}</table>
      </div>
    );
  },
  th({ children }) {
    return (
      <th className="border border-border px-3 py-1.5 text-left font-semibold">
        {children}
      </th>
    );
  },
  td({ children }) {
    return <td className="border border-border px-3 py-1.5">{children}</td>;
  },
};

export function ChatMarkdown({ content }: { content: string }) {
  return (
    <div className="prose-sm leading-relaxed">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
