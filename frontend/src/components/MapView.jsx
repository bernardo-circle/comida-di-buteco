import { useEffect, useMemo, useRef } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import { latLngBounds } from "leaflet";

const RIO_CENTER = [-22.9110137, -43.2093727];

function MapStateController({ records, selectedRecord }) {
  const map = useMap();
  const previousSelectedIdRef = useRef(null);

  useEffect(() => {
    if (selectedRecord?.lat && selectedRecord?.lng) {
      map.flyTo([selectedRecord.lat, selectedRecord.lng], 15, { duration: 1.1 });
      previousSelectedIdRef.current = selectedRecord.id;
      return;
    }

    if (!records.length) {
      map.setView(RIO_CENTER, 11);
      previousSelectedIdRef.current = null;
      return;
    }

    if (previousSelectedIdRef.current) {
      previousSelectedIdRef.current = null;
      return;
    }

    const points = records.filter((record) => record.lat && record.lng).map((record) => [record.lat, record.lng]);
    if (!points.length) {
      map.setView(RIO_CENTER, 11);
      return;
    }

    map.fitBounds(latLngBounds(points), { padding: [28, 28] });
  }, [map, records, selectedRecord]);

  return null;
}

function BrowseFocusController({ browseFocusRecord, browseFocusKey, selectedRecord }) {
  const map = useMap();
  const previousBrowseFocusKeyRef = useRef(null);

  useEffect(() => {
    if (selectedRecord) {
      return;
    }

    if (!browseFocusRecord?.lat || !browseFocusRecord?.lng || !browseFocusKey) {
      previousBrowseFocusKeyRef.current = null;
      return;
    }

    if (previousBrowseFocusKeyRef.current === browseFocusKey) {
      return;
    }

    previousBrowseFocusKeyRef.current = browseFocusKey;
    map.flyTo([browseFocusRecord.lat, browseFocusRecord.lng], 14, { duration: 0.9 });
  }, [browseFocusKey, browseFocusRecord, map, selectedRecord]);

  return null;
}

export default function MapView({ records, selectedId, selectedRecord, browseFocusRecord, browseFocusKey, onSelect }) {
  const mappableRecords = useMemo(
    () => records.filter((record) => typeof record.lat === "number" && typeof record.lng === "number"),
    [records],
  );

  return (
    <section className="map-panel">
      {!mappableRecords.length ? (
        <div className="map-empty-state">
          <strong>Nenhum ponto para exibir</strong>
          <p>Revise os filtros da busca para voltar a ver os butecos no mapa.</p>
        </div>
      ) : null}
      <MapContainer center={RIO_CENTER} zoom={11} className="map-root" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://stadiamaps.com/" target="_blank" rel="noreferrer">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank" rel="noreferrer">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>'
          url="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png"
          maxZoom={20}
        />
        {mappableRecords.map((record) => {
          const isSelected = record.id === selectedId;

          return (
            <CircleMarker
              key={record.id}
              center={[record.lat, record.lng]}
              radius={isSelected ? 11 : 8}
              pathOptions={{
                color: isSelected ? "#7a1f10" : "#8f3c1b",
                weight: isSelected ? 3 : 2,
                fillColor: isSelected ? "#f4c15d" : "#c85629",
                fillOpacity: isSelected ? 0.96 : 0.86,
              }}
              eventHandlers={{
                click: (event) => {
                  onSelect(record.id);
                  event.target.openPopup();
                },
                mouseover: (event) => {
                  event.target.openPopup();
                },
                mouseout: (event) => {
                  if (!isSelected) {
                    event.target.closePopup();
                  }
                },
              }}
            >
              <Popup>
                <div className="map-popup">
                  <strong>{record.name}</strong>
                  <span>{record.neighborhood || "Sem bairro"}</span>
                  <span>{record.address_normalized || record.address_raw}</span>
                  {record.dish_name ? <em>{record.dish_name}</em> : null}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
        <MapStateController records={mappableRecords} selectedRecord={selectedRecord} />
        <BrowseFocusController
          browseFocusRecord={browseFocusRecord}
          browseFocusKey={browseFocusKey}
          selectedRecord={selectedRecord}
        />
      </MapContainer>
    </section>
  );
}
