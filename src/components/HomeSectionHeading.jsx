export default function HomeSectionHeading({ id, className, children }) {
  return (
    <>
      <h2 id={id} className={`${className} home-section-title`}>{children}</h2>
      <div className="home-heading-divider" aria-hidden="true">
        <span />
        <img
          src={`${import.meta.env.BASE_URL}images/hero/straw-hat-skull.svg`}
          alt=""
          width="54"
          height="42"
        />
        <span />
      </div>
    </>
  );
}
