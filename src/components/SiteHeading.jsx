export default function SiteHeading({
  children,
  as: Tag = "h2",
  id,
  className = "",
  wrapperClassName = "",
  divider = true,
}) {
  return (
    <div className={`site-heading ${wrapperClassName}`.trim()}>
      <Tag id={id} className={`site-heading-title ${className}`.trim()}>
        {children}
      </Tag>
      {divider && (
        <div className="site-heading-divider" aria-hidden="true">
          <span />
          <img
            src={`${import.meta.env.BASE_URL}images/hero/straw-hat-skull.svg`}
            alt=""
            width="54"
            height="42"
          />
          <span />
        </div>
      )}
    </div>
  );
}
