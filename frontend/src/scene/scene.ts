/**
 * Three.js 描画層 — ユニットテスト免除ゾーン。
 * ここにはオブジェクト構築と描画ループだけを置き、計算・状態は logic/ に寄せる。
 */

import * as THREE from "three";

import { orbitPosition } from "../logic/orbit";

const ORBIT_RADIUS = 2;
const ORBIT_SPEED = 0.8; // rad/s

export function startScene(canvas: HTMLCanvasElement): void {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 3, 6);
  camera.lookAt(0, 0, 0);

  const cube = new THREE.Mesh(
    new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshStandardMaterial({ color: 0x4f9cff }),
  );
  scene.add(cube);

  scene.add(new THREE.AmbientLight(0xffffff, 0.4));
  const light = new THREE.DirectionalLight(0xffffff, 1.2);
  light.position.set(3, 5, 2);
  scene.add(light);

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  const start = performance.now();
  renderer.setAnimationLoop(() => {
    const t = (performance.now() - start) / 1000;
    const pos = orbitPosition(ORBIT_RADIUS, ORBIT_SPEED, t);
    cube.position.set(pos.x, pos.y, pos.z);
    cube.rotation.y = t;
    renderer.render(scene, camera);
  });
}
