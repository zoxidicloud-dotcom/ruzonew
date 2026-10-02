export function ComingSoon({ icon, title, description, note, botLink }) {
  return (
    <section className="coming-soon">
      <div className="coming-soon__icon">{icon}</div>
      <h2 className="coming-soon__title">{title}</h2>
      <p className="coming-soon__desc">{description}</p>
      {note && <p className="coming-soon__note">{note}</p>}
      {botLink && (
        <a className="coming-soon__cta" href={botLink} target="_blank" rel="noreferrer">
          Telegram botni ochish
        </a>
      )}
    </section>
  );
}
