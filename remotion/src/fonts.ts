// Vendored Latin fonts; render without Google Fonts requests.
// Keep fonts, brand.ts and brand.md aligned when changing the brand.
import {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

export const FONT_DISPLAY = 'Space Grotesk';
export const FONT_BODY = 'Inter';
export const FONT_MONO = 'JetBrains Mono';
export const FONT_SERIF = 'Spectral';

let fontsReady: Promise<void> | undefined;
function loadBundledFonts(): Promise<void> {
  if (!fontsReady) {
    const families: Array<[string, string, number[]]> = [
      [FONT_DISPLAY, 'SpaceGrotesk', [500, 600, 700]],
      [FONT_BODY, 'Inter', [400, 500, 600]],
      [FONT_MONO, 'JetBrainsMono', [400, 500, 700]],
      [FONT_SERIF, 'Spectral', [500, 600]],
    ];
    fontsReady = Promise.all(families.flatMap(([family, file, weights]) => weights.map(async (weight) => {
      const face = new FontFace(family, `url(${staticFile(`library/fonts/${file}-${weight}.woff2`)})`, {
        weight: String(weight), style: 'normal',
      });
      const fontSet = document.fonts as FontFaceSet & {add: (font: FontFace) => FontFaceSet};
      fontSet.add(await face.load());
    }))).then(() => undefined);
  }
  return fontsReady;
}

// Register after the composition mounts, not while the registry imports modules.
// Module-time handles could become orphaned and cancel an otherwise progressing
// render after 28 seconds. Each mounted composition owns and clears its own gate.
export function useBundledFonts() {
  const [handle] = useState(() => delayRender('Load bundled brand fonts'));
  useEffect(() => {
    loadBundledFonts().then(() => continueRender(handle)).catch(cancelRender);
  }, [handle]);
}
