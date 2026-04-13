function DetailValue({ value, fallback = "Não informado", multiline = false }) {
  if (!value) {
    return <dd className="detail-muted">{fallback}</dd>;
  }

  if (!multiline) {
    return <dd>{value}</dd>;
  }

  const parts = value.split(" | ").filter(Boolean);
  return (
    <dd className="detail-list">
      {parts.map((part) => (
        <span key={part}>{part}</span>
      ))}
    </dd>
  );
}

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
      {record.image_url ? (
        <img src={record.image_url} alt={record.name} className="details-image" />
      ) : (
        <div className="details-image details-image-fallback">
          <span>Sem imagem disponível</span>
        </div>
      )}
      <div className="details-copy">
        <p className="eyebrow">Selecionado</p>
        <h2>{record.name}</h2>
        <p>{record.address_normalized || record.address_raw}</p>
        <dl className="detail-grid">
          <div>
            <dt>Bairro</dt>
            <DetailValue value={record.neighborhood} fallback="Sem bairro" />
          </div>
          <div>
            <dt>Telefone</dt>
            <DetailValue value={record.phone} multiline />
          </div>
          <div>
            <dt>Horário</dt>
            <DetailValue value={record.hours} multiline />
          </div>
          <div>
            <dt>Petisco</dt>
            <DetailValue value={record.dish_name} />
          </div>
        </dl>
        <p className="dish-description">{record.dish_description || "Descrição do petisco não informada."}</p>
        <div className="detail-links">
          {record.detalhes_url ? (
            <a href={record.detalhes_url} target="_blank" rel="noreferrer">
              Página oficial
            </a>
          ) : null}
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
  onResetFilters,
}) {
  const selectedRecord = filteredRecords.find((record) => record.id === selectedId) || records.find((record) => record.id === selectedId) || null;
  const hasActiveFilters = Boolean(query.trim() || neighborhood);

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
        <div className="results-meta-row">
          <p>
            {filteredRecords.length} de {records.length} butecos visíveis
          </p>
          {hasActiveFilters ? (
            <button type="button" className="ghost-button" onClick={onResetFilters}>
              Limpar filtros
            </button>
          ) : null}
        </div>
      </section>

      <section className="results-list">
        {filteredRecords.length ? (
          filteredRecords.map((record) => (
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
          ))
        ) : (
          <div className="empty-results">
            <strong>Nenhum buteco encontrado</strong>
            <p>Tente outro nome ou remova o filtro de bairro para voltar ao conjunto completo.</p>
            {hasActiveFilters ? (
              <button type="button" className="ghost-button" onClick={onResetFilters}>
                Mostrar todos
              </button>
            ) : null}
          </div>
        )}
      </section>
    </aside>
  );
}
