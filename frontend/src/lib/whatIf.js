// Simple client-side linear recomputation using the deployed Ridge model's
// stored raw-space coefficients (see export_dashboard_data.py's
// get_what_if_inputs) - no live Python call. Only perturbs the SAME-MONTH
// crude oil / USD-INR inputs; lag and rolling context stay fixed, and the
// resulting shift is applied as a constant offset across the whole horizon.
// This is an approximation for exploring sensitivity, not a model refit.

export function computeShiftDollars(material, crudePct, fxPct) {
  const { baseCrudeOilPrice, baseUsdInrRate, crudeOilRawCoefficient, usdInrRawCoefficient } =
    material.whatIf;

  const crudeDelta = baseCrudeOilPrice * (crudePct / 100);
  const fxDelta = baseUsdInrRate * (fxPct / 100);

  return crudeOilRawCoefficient * crudeDelta + usdInrRawCoefficient * fxDelta;
}

export function shiftedForecastSeries(material, crudePct, fxPct) {
  if (crudePct === 0 && fxPct === 0) return null;
  const shift = computeShiftDollars(material, crudePct, fxPct);
  return material.forecast.map((row) => row.forecastedPrice + shift);
}
