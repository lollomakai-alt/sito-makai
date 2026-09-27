const navItems = [
  { name: "Chi siamo", id: "chi-siamo" },
  { name: "Menu", id: "menu" },
  { name: "Eventi", id: "eventi" },
  { name: "Galleria", id: "galleria", href: "/galleria" },
  { name: "Contatti", id: "contatti" },
];

export default function SiteNav({ activeSection }) {
  return (
    <nav className="top-nav">
      <a
        href="#"
        className="brand"
        onClick={(event) => {
          event.preventDefault();
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
      >
        <img
          src={`${import.meta.env.BASE_URL}images/Makai-grandline.PNG`}
          alt="Makai Grand Line"
          className="logo-full"
        />
      </a>
      <div className="nav-links">
        {navItems.map((item) => (
          <a
            key={item.id}
            href={item.href || `#${item.id}`}
            className={`nav-item ${activeSection === item.name ? "active" : ""}`}
          >
            {item.name}
          </a>
        ))}
      </div>
      <div className="lang-control">
        <span className="lang active">IT</span> | <span className="lang">EN</span>
      </div>
    </nav>
  );
}
