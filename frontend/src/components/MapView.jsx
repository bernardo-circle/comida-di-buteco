import { useEffect, useMemo } from "react";
import MarkerClusterGroup from "react-leaflet-cluster";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { latLngBounds } from "leaflet";

const RIO_CENTER = [-22.9110137, -43.2093727];

function MapStateController({ records, selectedRecord }) {
  const map = useMap();

  useEffect(() => {
    if (selectedRecord?.lat && selectedRecord?.lng) {
      map.flyTo([selectedRecord.lat, selectedRecord.lng], 15, { duration: 1.1 });
      return;
    }

    if (!records.length) {
      map.setView(RIO_CENTER, 11);
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

export default function MapView({ records, selectedId, onSelect }) {
  const selectedRecord = useMemo(
    () => records.find((record) => record.id === selectedId) || null,
    [records, selectedId],
  );

  const mappableRecords = useMemo(
    () => records.filter((record) => typeof record.lat === "number" && typeof record.lng === "number"),
    [records],
  );

  return (
    <section className="map-panel">
      <MapContainer center={RIO_CENTER} zoom={11} className="map-root" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MarkerClusterGroup chunkedLoading>
          {mappableRecords.map((record) => (
            <Marker
              key={record.id}
              position={[record.lat, record.lng]}
              eventHandlers={{
                click: () => onSelect(record.id),
              }}
            >
              <Popup>
                <strong>{record.name}</strong>
                <br />
                {record.neighborhood || "Sem bairro"}
                <br />
                {record.address_normalized || record.address_raw}
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
        <MapStateController records={mappableRecords} selectedRecord={selectedRecord} />
      </MapContainer>
    </section>
  );
}
