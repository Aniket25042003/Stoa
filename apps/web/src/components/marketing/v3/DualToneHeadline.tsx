import { cn } from "@/lib/cn";

type DualToneHeadlineProps = {
  primary: string;
  secondary?: string;
  as?: "h1" | "h2" | "h3";
  className?: string;
  primaryClassName?: string;
  secondaryClassName?: string;
};

export function DualToneHeadline({
  primary,
  secondary,
  as: Tag = "h1",
  className,
  primaryClassName,
  secondaryClassName,
}: DualToneHeadlineProps) {
  return (
    <Tag
      className={cn(
        "font-semibold tracking-[-0.02em] text-balance",
        Tag === "h1" && "text-[clamp(2.25rem,5.5vw,3.75rem)] leading-[1.08]",
        Tag === "h2" && "text-[clamp(1.75rem,4vw,2.75rem)] leading-[1.12]",
        Tag === "h3" && "text-xl leading-snug",
        className
      )}
    >
      <span className={cn("text-mkt-ink", primaryClassName)}>{primary}</span>
      {secondary ? (
        <>
          {" "}
          <span className={cn("text-mkt-ink-secondary", secondaryClassName)}>{secondary}</span>
        </>
      ) : null}
    </Tag>
  );
}
