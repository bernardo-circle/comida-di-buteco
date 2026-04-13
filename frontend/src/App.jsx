import { useEffect, useMemo, useState } from "react";
import { loadButecos } from "./api/dataLoader";
import MapView from "./components/MapView";
import Sidebar from "./components/Sidebar";

function searchKey(value) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

export default function App() {
  const [records, setRecords] = useState([]);
  const [status, setStatus] = useState("loading");
  const [query, setQuery] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    loadButecos()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setRecords(payload);
        setSelectedId(payload[0]?.id ?? null);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const neighborhoods = useMemo(() => {
    const values = new Set(records.map((record) => record.neighborhood).filter(Boolean));
    return [...values].sort((left, right) => left.localeCompare(right, "pt-BR"));
  }, [records]);

  const filteredRecords = useMemo(() => {
    const normalizedQuery = searchKey(query.trim());
    return records.filter((record) => {
      const matchesQuery = !normalizedQuery || searchKey(record.name).includes(normalizedQuery);
      const matchesNeighborhood = neighborhood ? record.neighborhood === neighborhood : true;
      return matchesQuery && matchesNeighborhood;
    });
  }, [records, query, neighborhood]);

  function resetFilters() {
    setQuery("");
    setNeighborhood("");
  }

  useEffect(() => {
    if (!filteredRecords.length) {
      setSelectedId(null);
      return;
    }

    const stillVisible = filteredRecords.some((record) => record.id === selectedId);
    if (!stillVisible) {
      setSelectedId(filteredRecords[0].id);
    }
  }, [filteredRecords, selectedId]);

  if (status === "loading") {
    return <main className="status-screen">Carregando butecos...</main>;
  }

  if (status === "error") {
    return <main className="status-screen">Nao foi possivel carregar o dataset.</main>;
  }

  return (
    <main className="app-shell">
      <Sidebar
        records={records}
        filteredRecords={filteredRecords}
        neighborhoods={neighborhoods}
        query={query}
        onQueryChange={setQuery}
        neighborhood={neighborhood}
        onNeighborhoodChange={setNeighborhood}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onResetFilters={resetFilters}
      />
      <MapView records={filteredRecords} selectedId={selectedId} onSelect={setSelectedId} />
    </main>
  );
}
