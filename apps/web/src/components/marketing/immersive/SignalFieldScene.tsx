/**
 * @file apps/web/src/components/marketing/immersive/SignalFieldScene.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Three.js
 */
"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Line, Sparkles } from "@react-three/drei";
import * as THREE from "three";

type SignalFieldProps = {
  variant?: "hero" | "ambient";
};

/** Lightweight node positions — marketing signal graph, not a solid orb */
const NODE_POSITIONS: [number, number, number][] = [
  [0, 0.3, 0],
  [-1.8, 0.9, -0.4],
  [1.6, 0.6, 0.2],
  [-1.2, -0.8, 0.5],
  [1.4, -0.5, -0.3],
  [0.2, 1.4, -0.6],
  [-0.5, -1.3, 0.1],
  [2.0, 0.1, -0.8],
];

const EDGES: [number, number][] = [
  [0, 1],
  [0, 2],
  [0, 3],
  [0, 4],
  [1, 5],
  [2, 7],
  [3, 6],
  [4, 7],
  [1, 3],
  [2, 4],
];

/**
 * Handles signal field scene behavior for this part of the Stoa application.
 *
 * @param variant - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function SignalFieldScene({ variant = "hero" }: SignalFieldProps) {
  const groupRef = useRef<THREE.Group>(null);
  const ringsRef = useRef<THREE.Group>(null);
  const pointer = useRef({ x: 0, y: 0 });

  const scale = variant === "ambient" ? 0.85 : 1;
  const sparkleCount = variant === "ambient" ? 24 : 36;

  const edgeLines = useMemo(
    () =>
      EDGES.map(([a, b], i) => ({
        key: `edge-${i}`,
        points: [NODE_POSITIONS[a], NODE_POSITIONS[b]] as [number, number, number][],
      })),
    []
  );

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    pointer.current.x = THREE.MathUtils.lerp(pointer.current.x, state.pointer.x * 0.35, 0.04);
    pointer.current.y = THREE.MathUtils.lerp(pointer.current.y, state.pointer.y * 0.25, 0.04);

    if (groupRef.current) {
      groupRef.current.rotation.y = pointer.current.x + time * 0.04;
      groupRef.current.rotation.x = pointer.current.y + Math.sin(time * 0.25) * 0.03;
    }
    if (ringsRef.current) {
      ringsRef.current.rotation.z = time * 0.06;
      ringsRef.current.rotation.x = Math.PI / 2.8 + pointer.current.y * 0.08;
    }
  });

  return (
    <group ref={groupRef} scale={scale}>
      {/* Thin orbital rings — wireframe only */}
      <group ref={ringsRef}>
        <mesh rotation={[Math.PI / 2.5, 0, 0]}>
          <torusGeometry args={[2.1, 0.012, 8, 96]} />
          <meshBasicMaterial color="#4F46E5" transparent opacity={0.35} />
        </mesh>
        <mesh rotation={[Math.PI / 3.2, 0.4, 0]}>
          <torusGeometry args={[1.55, 0.01, 8, 80]} />
          <meshBasicMaterial color="#4F46E5" transparent opacity={0.22} />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0.8, 0.15]}>
          <torusGeometry args={[2.45, 0.008, 6, 72]} />
          <meshBasicMaterial color="#E85D4C" transparent opacity={0.18} />
        </mesh>
      </group>

      {/* Signal edges */}
      {edgeLines.map((edge) => (
        <Line
          key={edge.key}
          points={edge.points}
          color="#4F46E5"
          transparent
          opacity={0.32}
          lineWidth={1}
        />
      ))}

      {/* Nodes */}
      {NODE_POSITIONS.map((pos, i) => (
        <mesh key={`node-${i}`} position={pos}>
          <sphereGeometry args={[i === 0 ? 0.07 : 0.045, 8, 8]} />
          <meshBasicMaterial
            color={i === 0 ? "#E85D4C" : "#4F46E5"}
            transparent
            opacity={i === 0 ? 0.9 : 0.65}
          />
        </mesh>
      ))}

      <Sparkles
        count={sparkleCount}
        scale={[8, 5, 4]}
        size={1.4}
        speed={0.2}
        opacity={0.35}
        color="#4F46E5"
      />
    </group>
  );
}
