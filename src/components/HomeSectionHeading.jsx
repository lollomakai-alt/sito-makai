import SiteHeading from "./SiteHeading";

export default function HomeSectionHeading({ id, className, children }) {
  return <SiteHeading id={id} className={className}>{children}</SiteHeading>;
}
