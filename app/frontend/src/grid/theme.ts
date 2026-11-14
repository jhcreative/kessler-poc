// AG Grid Community, themed to the house tokens (ADR 2026-11-14-ag-grid-for-grid-interfaces): never the stock look.
import {
  CellStyleModule,
  ClientSideRowModelModule,
  HighlightChangesModule,
  ModuleRegistry,
  NumberFilterModule,
  RowApiModule,
  RowStyleModule,
  TextFilterModule,
  themeQuartz,
} from "ag-grid-community";

// Only what the grids use (a performance budget, not AllCommunityModule): rows held in the browser, text and number
// filters, row lookup by id, and the flash on change. AG Grid's console names any module a feature needs.
ModuleRegistry.registerModules([
  CellStyleModule, // right-aligned money
  ClientSideRowModelModule,
  TextFilterModule,
  NumberFilterModule,
  RowApiModule,
  RowStyleModule, // the selected row in a queue
  HighlightChangesModule,
]);

export const houseGrid = themeQuartz.withParams({
  fontFamily: "IBM Plex Sans, Arial, sans-serif",
  headerFontFamily: "Roboto Condensed, Arial Narrow, sans-serif",
  headerFontWeight: 500,
  fontSize: 14,
  headerFontSize: 14,
  foregroundColor: "#333333",
  backgroundColor: "#ffffff",
  headerBackgroundColor: "#f7f7f8",
  borderColor: "#dddddd",
  accentColor: "#0066cc",
  rowHeight: 40,
  headerHeight: 40,
  borderRadius: 4,
  wrapperBorderRadius: 4,
  spacing: 6,
});
