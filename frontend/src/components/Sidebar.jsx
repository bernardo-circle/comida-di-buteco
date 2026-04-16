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

function SelectedButecoDetails({ record, onBack }) {
  return (
    <section className="sidebar-detail">
      <button type="button" className="ghost-button detail-back-button" onClick={onBack}>
        Voltar para a busca
      </button>

      {record.image_url ? (
        <img src={record.image_url} alt={record.name} className="sidebar-detail-image" />
      ) : (
        <div className="sidebar-detail-image sidebar-detail-image-fallback">
          <span>Sem imagem disponível</span>
        </div>
      )}

      <div className="sidebar-detail-copy">
        <p className="eyebrow">Buteco selecionado</p>
        <h2>{record.name}</h2>
        <p className="sidebar-detail-address">{record.address_normalized || record.address_raw}</p>

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

function SidebarHeader() {
  return (
    <div className="sidebar-header">
      <p className="eyebrow">Comida di Buteco</p>
      <p className="lede">Explore os butecos do Rio de Janeiro, filtre por bairro e navegue sem sair do mapa.</p>
    </div>
  );
}

function MobilePanelSwitcher({ hasSelection, mobilePanel, onChange }) {
  return (
    <section className="mobile-panel-switcher" aria-label="Alternar entre lista e detalhes">
      <button
        type="button"
        className={`mobile-panel-button ${mobilePanel === "browse" ? "active" : ""}`}
        onClick={() => onChange("browse")}
      >
        Explorar
      </button>
      <button
        type="button"
        className={`mobile-panel-button ${mobilePanel === "details" ? "active" : ""}`}
        onClick={() => onChange("details")}
        disabled={!hasSelection}
      >
        Detalhes
      </button>
    </section>
  );
}

function BrowseSidebar({
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
  const hasActiveFilters = Boolean(query.trim() || neighborhood);

  return (
    <section className="browse-sidebar">
      <section className="filters">
        <label className="control">
          <span>Buscar por nome do Buteco</span>
          <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Ex.: Cachambeer" />
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
    </section>
  );
}

export default function Sidebar(props) {
  const { selectedRecord, onBackToBrowse, isMobile, mobilePanel, onMobilePanelChange } = props;
  const hasSelection = Boolean(selectedRecord);

  let content;

  if (isMobile) {
    content =
      mobilePanel === "details" && hasSelection ? (
        <SelectedButecoDetails record={selectedRecord} onBack={() => onMobilePanelChange("browse")} />
      ) : (
        <BrowseSidebar {...props} />
      );
  } else {
    content = hasSelection ? <SelectedButecoDetails record={selectedRecord} onBack={onBackToBrowse} /> : <BrowseSidebar {...props} />;
  }

  return (
    <aside className={`sidebar ${selectedRecord ? "sidebar-detail-mode" : ""} ${isMobile ? "sidebar-mobile" : ""}`}>
      <SidebarHeader />
      {isMobile ? (
        <MobilePanelSwitcher hasSelection={hasSelection} mobilePanel={mobilePanel} onChange={onMobilePanelChange} />
      ) : null}
      {content}
    </aside>
  );
}
