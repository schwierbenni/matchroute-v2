import polyline from '@mapbox/polyline';

export const decodePolyline = (encoded) => {
  return polyline.decode(encoded).map(([lat, lng]) => ({ lat, lng }));
};