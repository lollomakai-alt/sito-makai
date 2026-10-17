import SiteHeading from "./SiteHeading";

export default function HeroStyleHeading({
  children,
  as: Tag = "h1",
  id,
  className = "",
  dividerClassName = "",
  divider = true,
}) {
  return <SiteHeading as={Tag} id={id} className={className} wrapperClassName={dividerClassName} divider={divider}>{children}</SiteHeading>;
}
