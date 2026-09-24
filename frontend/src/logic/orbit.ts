/**
 * Pure orbit math — このテンプレートの TDD スタイルを示すサンプル。
 * 実開発開始時に tests/orbit.test.ts と一緒に削除してよい。
 *
 * 描画に使う計算・状態はすべてこの logic/ 配下に置き、vitest でテストする。
 * scene/ には Three.js のオブジェクト構築と描画ループだけを置く。
 */

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

const TWO_PI = Math.PI * 2;

/** Normalize an angle in radians into the range [0, 2π). */
export function wrapAngle(rad: number): number {
  const wrapped = rad % TWO_PI;
  return wrapped < 0 ? wrapped + TWO_PI : wrapped;
}

/**
 * Position of a body orbiting the origin in the XZ plane.
 *
 * @param radius - orbit radius; must be >= 0
 * @param angularVelocity - radians per second (negative = clockwise)
 * @param tSeconds - elapsed time in seconds
 */
export function orbitPosition(radius: number, angularVelocity: number, tSeconds: number): Vec3 {
  if (radius < 0) {
    throw new RangeError(`radius must be >= 0, got ${radius}`);
  }
  const angle = wrapAngle(angularVelocity * tSeconds);
  return {
    x: radius * Math.cos(angle),
    y: 0,
    z: radius * Math.sin(angle),
  };
}
