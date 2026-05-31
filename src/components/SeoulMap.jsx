import seoulGeoJson from "../data/seoul_municipalities_geo_simple.json";
import { districtNameToId, districtIdToMeta } from "../data/seoulDistricts.js";

const viewBox = { width: 820, height: 760, padding: 32 };

// The GeoJSON file is stored locally so the map works without a runtime network call.
// Source: southkorea/seoul-maps, KOSTAT 2013 Seoul municipality boundaries.
// If you later replace it with a more detailed file, keep the same FeatureCollection
// shape and this component will continue to render it as SVG paths.
const allCoordinates = seoulGeoJson.features.flatMap((feature) =>
  flattenCoordinates(feature.geometry.coordinates)
);

const bounds = allCoordinates.reduce(
  (acc, [lon, lat]) => ({
    minLon: Math.min(acc.minLon, lon),
    maxLon: Math.max(acc.maxLon, lon),
    minLat: Math.min(acc.minLat, lat),
    maxLat: Math.max(acc.maxLat, lat)
  }),
  { minLon: Infinity, maxLon: -Infinity, minLat: Infinity, maxLat: -Infinity }
);

function flattenCoordinates(coordinates) {
  if (typeof coordinates[0]?.[0] === "number") {
    return coordinates;
  }

  return coordinates.flatMap((item) => flattenCoordinates(item));
}

function projectPoint([lon, lat]) {
  const drawableWidth = viewBox.width - viewBox.padding * 2;
  const drawableHeight = viewBox.height - viewBox.padding * 2;
  const x =
    viewBox.padding +
    ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * drawableWidth;
  const y =
    viewBox.padding +
    ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * drawableHeight;

  return [x, y];
}

function ringToPath(ring) {
  return ring
    .map((point, index) => {
      const [x, y] = projectPoint(point);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function geometryToPath(geometry) {
  const polygons = geometry.type === "MultiPolygon" ? geometry.coordinates : [geometry.coordinates];

  return polygons
    .map((polygon) => polygon.map((ring) => `${ringToPath(ring)} Z`).join(" "))
    .join(" ");
}

function signedRingArea(points) {
  let area = 0;

  for (let index = 0; index < points.length - 1; index += 1) {
    const [x1, y1] = points[index];
    const [x2, y2] = points[index + 1];
    area += x1 * y2 - x2 * y1;
  }

  return area / 2;
}

function ringCentroid(points) {
  let twiceArea = 0;
  let centerX = 0;
  let centerY = 0;

  for (let index = 0; index < points.length - 1; index += 1) {
    const [x1, y1] = points[index];
    const [x2, y2] = points[index + 1];
    const cross = x1 * y2 - x2 * y1;
    twiceArea += cross;
    centerX += (x1 + x2) * cross;
    centerY += (y1 + y2) * cross;
  }

  if (twiceArea === 0) {
    return points[0];
  }

  return [centerX / (3 * twiceArea), centerY / (3 * twiceArea)];
}

function projectedCentroid(feature) {
  const polygons = feature.geometry.type === "MultiPolygon"
    ? feature.geometry.coordinates
    : [feature.geometry.coordinates];
  const largestOuterRing = polygons
    .map((polygon) => polygon[0].map(projectPoint))
    .sort((a, b) => Math.abs(signedRingArea(b)) - Math.abs(signedRingArea(a)))[0];

  return ringCentroid(largestOuterRing);
}

// The computed polygon centroid is the baseline. Small visual offsets keep the
// dense downtown labels clear without changing any administrative boundary.
const labelNudges = {
  "jongno-gu": [8, -4],
  "jung-gu": [2, 7],
  "yongsan-gu": [0, 8],
  "seongdong-gu": [4, -2],
  "dongdaemun-gu": [5, 2],
  "yeongdeungpo-gu": [-3, 4],
  "geumcheon-gu": [-1, 5],
  "gangbuk-gu": [-4, 2],
  "dobong-gu": [0, 4],
  "gangseo-gu": [-8, 0],
  "seocho-gu": [2, 8],
  "gangnam-gu": [2, 2]
};

const districtFeatures = seoulGeoJson.features.map((feature) => {
  const id = districtNameToId[feature.properties.name];
  const [centroidX, centroidY] = projectedCentroid(feature);
  const [nudgeX = 0, nudgeY = 0] = labelNudges[id] ?? [];

  return {
    id,
    name: feature.properties.name,
    path: geometryToPath(feature.geometry),
    label: [centroidX + nudgeX, centroidY + nudgeY],
    meta: districtIdToMeta[id]
  };
});

export default function SeoulMap({ selectedDistrictId, onSelectDistrict }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-5">
      <svg
        viewBox={`0 0 ${viewBox.width} ${viewBox.height}`}
        role="img"
        aria-label="서울시 25개 자치구 인터랙티브 지도"
        className="h-auto w-full"
      >
        <rect
          width={viewBox.width}
          height={viewBox.height}
          rx="18"
          fill="currentColor"
          className="text-slate-50 dark:text-slate-950"
        />
        {districtFeatures.map((district) => (
          <g
            key={district.id}
            className="district-group"
            onClick={() => onSelectDistrict(district.id)}
          >
            <path
              id={district.id}
              d={district.path}
              className={`district-path ${
                selectedDistrictId === district.id ? "is-selected" : ""
              }`}
              fill={selectedDistrictId === district.id ? "#007bff" : "#cbd5e1"}
              stroke="#ffffff"
              strokeWidth="2.2"
              vectorEffect="non-scaling-stroke"
            />
            <text
              x={district.label[0]}
              y={district.label[1]}
              textAnchor="middle"
              dominantBaseline="central"
              className={`district-label text-[11px] font-bold ${
                selectedDistrictId === district.id
                  ? "district-label-selected fill-white"
                  : "fill-slate-700 dark:fill-slate-100"
              }`}
            >
              {district.name}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
