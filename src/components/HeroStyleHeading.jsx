export default function HeroStyleHeading({
  children,
  as: Tag = "h1",
  id,
  className = "",
  dividerClassName = "",
  divider = true,
}) {
  return (
    <div className={`hero-style-heading ${className}`.trim()}>
      <Tag id={id} className="hero-style-title">
        {children}
      </Tag>
      {divider && (
        <div className={`hero-style-divider ${dividerClassName}`.trim()} aria-hidden="true">
          <img
            src={`${import.meta.env.BASE_URL}images/hero/straw-hat-skull.svg`}
            alt=""
            width="54"
            height="42"
          />
        </div>
      )}
    </div>
  );
}