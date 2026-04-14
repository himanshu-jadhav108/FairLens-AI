interface Props {
  text: string;
}

export default function MarkdownRenderer({ text }: Props) {
  const lines = text.split("\n");

  return (
    <div className="space-y-2 leading-relaxed" style={{ lineHeight: 1.8 }}>
      {lines.map((line, i) => {
        const trimmed = line.trim();

        if (trimmed === "---") {
          return <hr key={i} className="border-border my-4" />;
        }

        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={i} className="font-display text-[13px] text-foreground-secondary mt-4 mb-1">
              {renderInline(trimmed.slice(4))}
            </h4>
          );
        }

        if (trimmed.startsWith("## ")) {
          return (
            <h3 key={i} className="font-display text-[16px] font-bold text-primary mt-5 mb-2">
              {renderInline(trimmed.slice(3))}
            </h3>
          );
        }

        if (trimmed.startsWith("> ")) {
          return (
            <blockquote key={i} className="border-l-2 border-primary pl-4 italic text-foreground-muted text-sm my-2">
              {renderInline(trimmed.slice(2))}
            </blockquote>
          );
        }

        if (trimmed === "") {
          return <div key={i} className="h-2" />;
        }

        return (
          <p key={i} className="font-mono text-[13px] text-foreground-secondary">
            {renderInline(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="text-foreground font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}
