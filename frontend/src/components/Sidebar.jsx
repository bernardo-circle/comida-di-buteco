function DetailsCard({ record }) {
  if (!record) {
    return (
      <section className="details-card empty">
        <h2>Nenhum buteco selecionado</h2>
        <p>Escolha um item na lista ou clique em um marcador no mapa.</p>
      </section>
    );
  }

  return (
    <section className="details-card">
      {record.image_url ? <img src={record.image_url} alt={record.name} className="details-image" /> : null}
      <div className="details-copy">
        <p className="eyebrow">Selecionado</p>
        <h2>{record.name}</h2>
        <p>{record.address_normalized || record.address_raw}</p>
        <dl className="detail-grid">
          <div>
            <dt>Bairro</dt>
            <dd>{record.neighborhood || "Sem bairro"}</dd>
          </div>
          <div>
            <dt>Telefone</dt>
            <dd>{record.phone || "Não informado"}</dd>
          </div>
          <div>
            <dt>Horário</dt>
            <dd>{record.hours || "Não informado"}</dd>
          </div>
          <div>
            <dt>Petisco</dt>
            <dd>{record.dish_name || "Não informado"}</dd>
          </div>
        </dl>
        {record.dish_description ? <p className="dish-description">{record.dish_description}</p> : null}
        <div className="detail-links">
          <a href={record.detalhes_url} target="_blank" rel="noreferrer">
            Página oficial
          </a>
          {record.maps_url ? (
            <a href={record.maps_url} target="_blank" rel="noreferrer">
              Como chegar
            </a>
          ) : null}
        </div>
      </div>
    </section>
  );
}

export default function Sidebar({
  records,
  filteredRecords,
  neighborhoods,
  query,
  onQueryChange,
  neighborhood,
  onNeighborhoodChange,
  selectedId,
  onSelect,
}) {
  const selectedRecord = filteredRecords.find((record) => record.id === selectedId) || records.find((record) => record.id === selectedId) || null;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <p className="eyebrow">Comida di Buteco</p>
        <h1>Rio no mapa</h1>
        <p className="lede">
          Explore os butecos do Rio de Janeiro, filtre por bairro e abra os detalhes sem sair do mapa.
        </p>
      </div>

      <DetailsCard record={selectedRecord} />

      <section className="filters">
        <label className="control">
          <span>Buscar por nome</span>
          <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Ex.: Baixo Gago" />
        </label>

        <label className="control">
          <span>Filtrar por bairro</span>
          <select value={neighborhood} onChange={(event) => onNeighborhoodChange(event.target.value)}>
            <option value="">Todos os bairros</option>
            {neighborhoods.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="results-meta">
        <p>{filteredRecords.length} butecos visíveis</p>
      </section>

      <section className="results-list">
        {filteredRecords.map((record) => (
          <button
            key={record.id}
            type="button"
            className={`result-item ${record.id === selectedId ? "active" : ""}`}
            onClick={() => onSelect(record.id)}
          >
            <strong>{record.name}</strong>
            <span>{record.neighborhood || "Sem bairro"}</span>
            <small>{record.address_normalized || record.address_raw}</small>
          </button>
        ))}
      </section>
    </aside>
  );
}
