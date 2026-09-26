"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { EntityRecord, InteractiveManifest, NavigationMode } from "../runtime/types";
import { heightLabel, searchPlaces, typeLabel } from "./placeState";

type Panel = "search" | "place" | "help" | "about" | null;

export function ProductShell({ interactive, navigation, selectedEntity, tourStops, tourIndex, ready, onMode, onSelectPlace, onClosePlace, onTourStop, onShare, onFocusPlace }: {
  interactive: InteractiveManifest; navigation: NavigationMode; selectedEntity: EntityRecord | null; tourStops: EntityRecord[]; tourIndex: number; ready: boolean;
  onMode: (mode: NavigationMode) => void; onSelectPlace: (entity: EntityRecord) => void; onClosePlace: () => void; onTourStop: (index: number) => void; onShare: () => void; onFocusPlace: () => void;
}) {
  const [panel, setPanel] = useState<Panel>(null);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [intro, setIntro] = useState(false);
  const [locked, setLocked] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchButton = useRef<HTMLButtonElement>(null);
  const helpButton = useRef<HTMLButtonElement>(null);
  const aboutButton = useRef<HTMLButtonElement>(null);
  const placeHeading = useRef<HTMLHeadingElement>(null);
  const placeReturnToSearch = useRef(false);
  const results = useMemo(() => searchPlaces(interactive.entities, query), [interactive, query]);
  const validActiveIndex = results.length ? Math.min(activeIndex, results.length - 1) : -1;
  const snapshotDate = /bgc-(\d{4})-(\d{2})-(\d{2})/.exec(interactive.source_snapshot);
  const snapshotLabel = snapshotDate
    ? new Intl.DateTimeFormat("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" }).format(new Date(`${snapshotDate[1]}-${snapshotDate[2]}-${snapshotDate[3]}T00:00:00Z`))
    : "date unavailable";

  useEffect(() => {
    const initialize = window.setTimeout(() => {
      const params = new URLSearchParams(window.location.search);
      if (params.has("place") || params.has("tour") || params.has("mode")) return;
      try { setIntro(localStorage.getItem("bgc3d-intro-seen") !== "1"); } catch { setIntro(true); }
    }, 0);
    const change = () => setLocked(Boolean(document.pointerLockElement));
    document.addEventListener("pointerlockchange", change);
    return () => { window.clearTimeout(initialize); document.removeEventListener("pointerlockchange", change); };
  }, []);
  useEffect(() => { if (selectedEntity) { const timer = window.setTimeout(() => setPanel("place"), 0); return () => window.clearTimeout(timer); } }, [selectedEntity]);
  useEffect(() => { if (panel === "search") inputRef.current?.focus(); }, [panel]);
  useEffect(() => { if (panel === "place" && placeReturnToSearch.current) placeHeading.current?.focus(); }, [panel]);
  function closePanel() {
    if (panel === "place") {
      onClosePlace();
      if (placeReturnToSearch.current) searchButton.current?.focus();
      placeReturnToSearch.current = false;
    } else if (panel === "search") searchButton.current?.focus();
    else if (panel === "help") helpButton.current?.focus();
    else if (panel === "about") aboutButton.current?.focus();
    setPanel(null);
  }
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || document.pointerLockElement) return;
      if (panel) { event.preventDefault(); closePanel(); }
      else if (intro) { event.preventDefault(); dismissIntro(); }
    };
    window.addEventListener("keydown", keydown);
    return () => window.removeEventListener("keydown", keydown);
  });
  function dismissIntro() { setIntro(false); try { localStorage.setItem("bgc3d-intro-seen", "1"); } catch {} }
  function choose(entity: EntityRecord) { placeReturnToSearch.current = true; onSelectPlace(entity); setPanel("place"); setQuery(""); }
  function changeMode(mode: NavigationMode) { if (intro) dismissIntro(); setPanel(null); onMode(mode); }
  function openPanel(next: Panel) {
    if (intro) dismissIntro();
    if (navigation !== "INSPECT") onMode("INSPECT");
    if (next === "search" && panel !== "search") { setQuery(""); setActiveIndex(0); }
    setPanel((current) => current === next ? null : next);
  }

  return <>
    <header className="product-header">
      <div className="product-brand"><span className="brand-mark">BGC<span>3D</span></span><span className="brand-subtitle">Explore Bonifacio Global City</span></div>
      <nav className="primary-controls" aria-label="Explore modes">
        <button type="button" className={navigation === "INSPECT" ? "active" : ""} aria-current={navigation === "INSPECT" ? "page" : undefined} onClick={() => changeMode("INSPECT")}>Explore</button>
        <button id="walk-lock-button" type="button" className={navigation === "WALK" ? "active" : ""} aria-current={navigation === "WALK" ? "page" : undefined} onClick={() => changeMode("WALK")}>Walk</button>
        <button type="button" className={navigation === "TOUR" ? "active" : ""} aria-current={navigation === "TOUR" ? "page" : undefined} onClick={() => changeMode("TOUR")} disabled={!tourStops.length}>Tour</button>
      </nav>
      <div className="header-actions"><button ref={searchButton} type="button" onClick={() => openPanel("search")} aria-expanded={panel === "search"}>Search</button><button ref={helpButton} type="button" onClick={() => openPanel("help")} aria-expanded={panel === "help"}>Help</button><button ref={aboutButton} type="button" onClick={() => openPanel("about")} aria-expanded={panel === "about"}>About</button></div>
    </header>

    {intro ? <aside className="intro-card" aria-label="Welcome to BGC 3D"><span className="eyebrow">Explore the city</span><h1>BGC in three dimensions.</h1><p>Search places, walk the streets, or follow a guided tour.</p><button type="button" onClick={dismissIntro}>Explore BGC</button></aside> : null}
    {navigation === "INSPECT" && !intro && !panel ? <div className="control-hint">Drag to rotate <span>·</span> Scroll to zoom <span>·</span> Select a building</div> : null}
    {navigation === "WALK" ? <aside className="walk-help" aria-live="polite"><strong>{locked ? "Walking" : "Ready to walk"}</strong><span className="walk-desktop-instructions">{locked ? "WASD move · Shift faster · Esc release" : "Click the city to control the camera. WASD move, Shift faster, Esc release."}</span><span className="walk-touch-instructions">Desktop Walk controls are not yet available on touch devices.</span></aside> : null}
    {navigation === "TOUR" && tourStops[tourIndex] ? <aside className="tour-panel" aria-label="Guided tour"><span className="eyebrow">BGC landmarks · Stop {tourIndex + 1} of {tourStops.length}</span><strong>{tourStops[tourIndex].name}</strong><div><button type="button" disabled={tourIndex === 0} onClick={() => onTourStop(tourIndex - 1)}>Previous</button><button type="button" disabled={tourIndex === tourStops.length - 1} onClick={() => onTourStop(tourIndex + 1)}>Next</button><button type="button" onClick={() => changeMode("INSPECT")}>Exit</button></div></aside> : null}

    {panel === "search" ? <aside className="product-panel search-panel" aria-label="Search named places"><div className="panel-heading"><div><span className="eyebrow">Find a place</span><h2>Search BGC</h2></div><button type="button" className="panel-close" aria-label="Close search" onClick={closePanel}>Close</button></div><label htmlFor="place-search">Place name</label><input ref={inputRef} id="place-search" role="combobox" aria-autocomplete="list" aria-expanded={results.length > 0} aria-controls={results.length ? "place-results" : undefined} aria-activedescendant={validActiveIndex >= 0 ? `place-option-${validActiveIndex}` : undefined} value={query} onChange={(event) => { setQuery(event.target.value); setActiveIndex(0); }} onKeyDown={(event) => { if (event.key === "ArrowDown" && results.length) { event.preventDefault(); setActiveIndex((index) => Math.min(results.length - 1, index + 1)); } else if (event.key === "ArrowUp" && results.length) { event.preventDefault(); setActiveIndex((index) => Math.max(0, index - 1)); } else if (event.key === "Enter" && validActiveIndex >= 0) { event.preventDefault(); choose(results[validActiveIndex]); } }} placeholder="Try Central Square" autoComplete="off" />{results.length ? <div id="place-results" role="listbox" className="search-results">{results.map((entity, index) => <button id={`place-option-${index}`} role="option" aria-selected={index === validActiveIndex} key={entity.entity_id} type="button" onMouseEnter={() => setActiveIndex(index)} onClick={() => choose(entity)}><strong>{entity.name}</strong><span>{typeLabel(entity.building_type)}</span></button>)}</div> : <p className="search-status" role={query ? "status" : undefined}>{query ? "No matching named place in the current BGC dataset." : `Search ${interactive.entities.length} named places in the current dataset.`}</p>}</aside> : null}

    {panel === "place" && selectedEntity && navigation !== "TOUR" ? <aside className="product-panel selection-panel" aria-label="Place details"><div className="panel-heading"><span className="eyebrow">Place details</span><button type="button" className="panel-close" onClick={closePanel} aria-label="Close place details">Close</button></div><h2 ref={placeHeading} tabIndex={-1}>{selectedEntity.name ?? "Unnamed building"}</h2><p className="place-type">{typeLabel(selectedEntity.building_type)}</p><dl><div><dt>Height</dt><dd>{heightLabel(selectedEntity)}</dd></div></dl><p className="data-note">This model uses mapped footprints. Background heights may be approximate.</p><div className="panel-actions"><button type="button" onClick={onFocusPlace}>View place</button><button type="button" onClick={onShare}>Share</button></div></aside> : null}

    {panel === "help" ? <aside className="product-panel info-panel" aria-label="Help"><div className="panel-heading"><div><span className="eyebrow">Getting around</span><h2>Help</h2></div><button type="button" className="panel-close" onClick={closePanel}>Close</button></div><h3>Explore</h3><p>Left drag to pan, right drag to rotate or tilt, and scroll to zoom. Select a building to see details. Search finds named places in the current dataset.</p><h3>Walk</h3><p>On desktop, select Walk and click the city to control the camera. Use WASD to move, Shift to move faster, and Esc to release the pointer.</p><h3>Tour</h3><p>Follow seven modeled landmarks using Previous and Next. Exit returns to Explore.</p></aside> : null}
    {panel === "about" ? <aside className="product-panel info-panel" aria-label="About and data"><div className="panel-heading"><div><span className="eyebrow">About the model</span><h2>About &amp; data</h2></div><button type="button" className="panel-close" onClick={closePanel}>Close</button></div><p>BGC 3D is an exploratory city model built primarily from geographic open data. Some selected landmarks have additional modeling. Many background heights and generic street objects are approximate.</p><p>The project boundary is estimated. This experience is not survey grade and should not be used for legal or engineering decisions.</p><p>Geographic data snapshot: {snapshotLabel}. Search covers {interactive.entities.length} named places.</p><button type="button" onClick={onShare}>Share BGC 3D</button></aside> : null}
    {!ready ? <div className="loading-pill" role="status">Preparing nearby buildings</div> : null}
  </>;
}
