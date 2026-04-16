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

function useIsMobile(breakpoint = 900) {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }

    return window.matchMedia(`(max-width: ${breakpoint}px)`).matches;
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }

    const mediaQuery = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const updateMatch = (event) => {
      setIsMobile(event.matches);
    };

    setIsMobile(mediaQuery.matches);

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", updateMatch);
      return () => mediaQuery.removeEventListener("change", updateMatch);
    }

    mediaQuery.addListener(updateMatch);
    return () => mediaQuery.removeListener(updateMatch);
  }, [breakpoint]);

  return isMobile;
}

export default function App() {
  const [records, setRecords] = useState([]);
  const [status, setStatus] = useState("loading");
  const [query, setQuery] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [mobilePanel, setMobilePanel] = useState("browse");
  const isMobile = useIsMobile();

  useEffect(() => {
    let cancelled = false;

    loadButecos()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setRecords(payload);
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

  const selectedRecord = useMemo(
    () => filteredRecords.find((record) => record.id === selectedId) || records.find((record) => record.id === selectedId) || null,
    [filteredRecords, records, selectedId],
  );

  const browseFocusRecord = useMemo(() => {
    if (!neighborhood || isDetailOpen) {
      return null;
    }

    return filteredRecords[0] ?? null;
  }, [filteredRecords, isDetailOpen, neighborhood]);

  const browseFocusKey = neighborhood ? `${neighborhood}:${browseFocusRecord?.id ?? "none"}` : null;

  function resetFilters() {
    setQuery("");
    setNeighborhood("");
  }

  function openButecoDetails(id) {
    setSelectedId(id);
    setIsDetailOpen(true);

    if (isMobile) {
      setMobilePanel("details");
    }
  }

  useEffect(() => {
    if (!filteredRecords.length) {
      setSelectedId(null);
      setIsDetailOpen(false);
      return;
    }

    if (selectedId === null) {
      return;
    }

    const stillVisible = filteredRecords.some((record) => record.id === selectedId);
    if (!stillVisible) {
      setSelectedId(null);
      setIsDetailOpen(false);
    }
  }, [filteredRecords, selectedId]);

  useEffect(() => {
    if (!isMobile) {
      setMobilePanel("browse");
      return;
    }

    if (!selectedRecord) {
      setMobilePanel("browse");
    }
  }, [isMobile, selectedRecord]);

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
        selectedRecord={isDetailOpen ? selectedRecord : null}
        onSelect={openButecoDetails}
        onBackToBrowse={() => {
          setIsDetailOpen(false);
          setSelectedId(null);
        }}
        onResetFilters={resetFilters}
        isMobile={isMobile}
        mobilePanel={mobilePanel}
        onMobilePanelChange={setMobilePanel}
      />
      <MapView
        records={filteredRecords}
        selectedId={selectedId}
        selectedRecord={selectedRecord}
        browseFocusRecord={browseFocusRecord}
        browseFocusKey={browseFocusKey}
        onSelect={openButecoDetails}
      />
    </main>
  );
}
