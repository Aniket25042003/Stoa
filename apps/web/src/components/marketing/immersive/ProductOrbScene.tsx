"use client";

import { useMemo, useRef, useLayoutEffect } from "react";
import { useFrame } from "@react-three/fiber";
import { ContactShadows, Float, useTexture } from "@react-three/drei";
import * as THREE from "three";
import { ORB_FACE_IMAGES } from "@/lib/landingFeatures";

const FACE_COUNT = 6;
const FACE_ANGLE = (Math.PI * 2) / FACE_COUNT;
/** Circumradius — vertices of the hex sit on this circle */
const ORB_RADIUS = 1.28;
/** Square faces so 1:1 textures map without stretch */
const FACE_SIZE = ORB_RADIUS;
const APOTHEM = ORB_RADIUS * Math.cos(Math.PI / FACE_COUNT);
/** Slight overlap to eliminate hairline seams between faces */
const FACE_PLANE = FACE_SIZE * 1.006;
/** Face 0 centered toward +Z at scroll section 0 */
const ROTATION_OFFSET = 0;

type ProductOrbSceneProps = {
  scrollProgress: number;
  activeSection: number;
};

function configureTexture(tex: THREE.Texture, maxAnisotropy: number) {
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = maxAnisotropy;
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.generateMipmaps = true;
  tex.flipY = true;
}

export function ProductOrbScene({ scrollProgress, activeSection }: ProductOrbSceneProps) {
  const groupRef = useRef<THREE.Group>(null);
  const rotationRef = useRef(0);
  const pointer = useRef({ x: 0, y: 0 });
  const materialsRef = useRef<THREE.MeshStandardMaterial[]>([]);

  const textures = useTexture([...ORB_FACE_IMAGES]);

  const faceTransforms = useMemo(() => {
    return Array.from({ length: FACE_COUNT }, (_, i) => {
      const angle = i * FACE_ANGLE;
      return {
        index: i,
        position: [APOTHEM * Math.sin(angle), 0, APOTHEM * Math.cos(angle)] as [
          number,
          number,
          number,
        ],
        rotationY: angle,
      };
    });
  }, []);

  const capGeometry = useMemo(
    () => new THREE.CircleGeometry(ORB_RADIUS * 0.92, FACE_COUNT),
    []
  );

  const rimGeometry = useMemo(
    () => new THREE.TorusGeometry(APOTHEM * 1.02, 0.016, 8, FACE_COUNT),
    []
  );

  const materials = useMemo(
    () =>
      textures.map(
        (_, i) =>
          new THREE.MeshStandardMaterial({
            map: textures[i],
            emissiveMap: textures[i],
            emissive: new THREE.Color("#ffffff"),
            emissiveIntensity: 0.42,
            roughness: 0.92,
            metalness: 0,
            side: THREE.FrontSide,
          })
      ),
    [textures]
  );

  materialsRef.current = materials;

  const capMaterial = useMemo(
    () =>
      new THREE.MeshPhysicalMaterial({
        color: "#FAF8F4",
        transparent: true,
        opacity: 0.28,
        roughness: 0.2,
        metalness: 0,
        transmission: 0.08,
        clearcoat: 0.35,
      }),
    []
  );

  useLayoutEffect(() => {
    const maxAnisotropy = 16;
    textures.forEach((tex, i) => {
      configureTexture(tex, maxAnisotropy);
      const mat = materials[i];
      if (mat) {
        mat.map = tex;
        mat.emissiveMap = tex;
        mat.needsUpdate = true;
      }
    });
  }, [textures, materials]);

  useLayoutEffect(() => {
    materials.forEach((mat, i) => {
      const isActive = i === activeSection;
      mat.emissive.set("#ffffff");
      mat.emissiveIntensity = isActive ? 0.58 : 0.48;
      mat.color.set("#ffffff");
      mat.transparent = false;
      mat.opacity = 1;
    });
  }, [activeSection, materials]);

  const maxSection = FACE_COUNT - 1;
  const targetRotation = scrollProgress * maxSection * FACE_ANGLE + ROTATION_OFFSET;

  useFrame((state) => {
    rotationRef.current = THREE.MathUtils.lerp(rotationRef.current, targetRotation, 0.08);

    pointer.current.x = THREE.MathUtils.lerp(pointer.current.x, state.pointer.x * 0.08, 0.04);
    pointer.current.y = THREE.MathUtils.lerp(pointer.current.y, state.pointer.y * 0.05, 0.04);

    if (groupRef.current) {
      groupRef.current.rotation.y = rotationRef.current + pointer.current.x;
      groupRef.current.rotation.x = pointer.current.y * 0.1;
    }
  });

  return (
    <>
      <Float speed={1.1} rotationIntensity={0.02} floatIntensity={0.15}>
        <group ref={groupRef}>
          {/* Six square planes — perfect 1:1 texture mapping, flush hex faces */}
          {faceTransforms.map((face) => (
            <mesh
              key={`face-${face.index}`}
              position={face.position}
              rotation={[0, face.rotationY, 0]}
            >
              <planeGeometry args={[FACE_PLANE, FACE_PLANE]} />
              <primitive object={materials[face.index]} attach="material" />
            </mesh>
          ))}

          {/* Frosted hex caps */}
          <mesh position={[0, FACE_SIZE / 2, 0]} rotation={[-Math.PI / 2, 0, 0]} geometry={capGeometry}>
            <primitive object={capMaterial} attach="material" />
          </mesh>
          <mesh
            position={[0, -FACE_SIZE / 2, 0]}
            rotation={[Math.PI / 2, 0, 0]}
            geometry={capGeometry}
          >
            <primitive object={capMaterial.clone()} attach="material" />
          </mesh>

          {/* Equator ring */}
          <mesh geometry={rimGeometry} rotation={[Math.PI / 2, 0, 0]}>
            <meshStandardMaterial
              color="#6D66F0"
              emissive="#4F46E5"
              emissiveIntensity={0.22}
              transparent
              opacity={0.38}
              metalness={0.45}
              roughness={0.18}
            />
          </mesh>

          {/* Inner core — kept subtle so face art stays readable */}
          <mesh>
            <sphereGeometry args={[0.14, 20, 20]} />
            <meshStandardMaterial
              color="#4F46E5"
              emissive="#4F46E5"
              emissiveIntensity={0.18}
              transparent
              opacity={0.14}
            />
          </mesh>
        </group>
      </Float>

      <ContactShadows
        position={[0, -0.85, 0]}
        opacity={0.08}
        scale={5}
        blur={3.6}
        far={3}
        color="#c8c4bc"
      />
    </>
  );
}
