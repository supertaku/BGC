"use client";

import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import { distanceToTileBounds } from "./spatial";
import { stability } from "./stability";
import { chooseStableWay } from "./streetLogic";
import type { CurrentStreet, NavigationMode, RuntimeRefs } from "./types";

const QUERY_INTERVAL_S = 0.25;
const TILE_RADIUS_M = 125;
const MOVEMENT_M = 1.5;

export function StreetLocator({ mode, refs, onStreetChange }: {
  mode: NavigationMode;
  refs: RuntimeRefs;
  onStreetChange: (street: CurrentStreet | null) => void;
}) {
  const { camera } = useThree();
  const elapsed = useRef(0);
  const lastPosition = useRef<[number, number] | null>(null);
  const currentId = useRef<string | null>(null);
  const lastCandidateCount = useRef(-1);

  useEffect(() => {
    if (mode === "WALK") { elapsed.current = QUERY_INTERVAL_S; return; }
    lastPosition.current = null;
    currentId.current = null;
    onStreetChange(null);
    stability.current_street_id = null;
    stability.current_street_name = null;
    stability.current_street_distance_m = null;
  }, [mode, onStreetChange]);

  useFrame((_, delta) => {
    if (mode !== "WALK") return;
    elapsed.current += delta;
    if (elapsed.current < QUERY_INTERVAL_S) return;
    elapsed.current = 0;
    const position: [number, number] = [camera.position.x, camera.position.z];
    const candidates = [...refs.tileRecords.current.values()]
      .filter((tile) => refs.sidecars.current.has(tile.tile_id) && distanceToTileBounds(position[0], position[1], tile) <= TILE_RADIUS_M)
      .flatMap((tile) => refs.sidecars.current.get(tile.tile_id)?.namedWays ?? []);
    if (currentId.current && lastPosition.current && lastCandidateCount.current === candidates.length &&
        Math.hypot(position[0] - lastPosition.current[0], position[1] - lastPosition.current[1]) < MOVEMENT_M) return;
    lastPosition.current = position;
    lastCandidateCount.current = candidates.length;
    stability.street_queries++;
    stability.street_candidate_segments = candidates.length;
    const result = chooseStableWay(position, candidates, currentId.current);
    const nextId = result?.way.id ?? null;
    stability.current_street_distance_m = result?.distance_m ?? null;
    if (nextId === currentId.current) return;
    currentId.current = nextId;
    stability.street_changes++;
    stability.current_street_id = nextId;
    stability.current_street_name = result?.way.name ?? null;
    onStreetChange(result ? { id: result.way.id, name: result.way.name, kind: result.way.kind } : null);
  });
  return null;
}
