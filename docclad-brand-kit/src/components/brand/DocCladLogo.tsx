import type { ImgHTMLAttributes } from "react";

type LogoVariant = "primary" | "white" | "black";
type LogoLayout = "full" | "mark";

export interface DocCladLogoProps
  extends Omit<ImgHTMLAttributes<HTMLImageElement>, "src" | "alt"> {
  variant?: LogoVariant;
  layout?: LogoLayout;
  alt?: string;
}

export function DocCladLogo({
  variant = "primary",
  layout = "full",
  alt = "DocClad",
  className = "",
  ...props
}: DocCladLogoProps) {
  const file =
    layout === "mark"
      ? variant === "white"
        ? "docclad-mark-white.svg"
        : variant === "black"
          ? "docclad-mark-black.svg"
          : "docclad-mark-primary.svg"
      : variant === "white"
        ? "docclad-logo-white.svg"
        : variant === "black"
          ? "docclad-logo-black.svg"
          : "docclad-logo-primary.svg";

  return (
    <img
      src={`/brand/${file}`}
      alt={alt}
      className={`block h-auto w-auto object-contain ${className}`}
      draggable={false}
      {...props}
    />
  );
}
