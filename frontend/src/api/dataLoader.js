function normalizeRecord(record) {
  return {
    ...record,
    lat: typeof record.lat === "number" ? record.lat : record.lat ? Number(record.lat) : null,
    lng: typeof record.lng === "number" ? record.lng : record.lng ? Number(record.lng) : null,
    neighborhood: record.neighborhood || "Sem bairro",
  };
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}`);
  }
  return response.json();
}

export async function loadButecos() {
  try {
    const liveData = await fetchJson("/api/butecos");
    return liveData.map(normalizeRecord);
  } catch {
    const sampleData = await fetchJson("/data/rio_butecos_sample.json");
    return sampleData.map(normalizeRecord);
  }
}
