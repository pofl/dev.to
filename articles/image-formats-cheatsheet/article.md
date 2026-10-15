---
{
  "devto_id": null,
  "title": "Image formats cheatsheet: JPEG, PNG, WebP, AVIF, HEIC, JXL",
  "published": false,
  "description": "A quick comparison of JPEG, PNG, WebP, AVIF, HEIC and JPEG XL: compression, speed, licensing and when to use each.",
  "tags": "webdev, images, performance, cheatsheet",
  "canonical_url": null,
  "main_image": null,
  "series": null,
  "organization_id": null
}
---
Image formats cheatsheet: JPEG, PNG, WebP, AVIF, HEIC, JXL


## Comparison

| Format | Size vs JPEG (same quality) | Lossy / Lossless | Alpha / HDR / Anim | Encode | Decode | License / patents | Support |
|---|---|---|---|---|---|---|---|
| **JPEG** | baseline | Lossy (lossless rare) | No / No / No | Very fast | Very fast | Free, patents expired | Universal |
| **PNG** | Much larger for photos | Lossless | Yes / No / APNG | Fast | Fast | Free, open | Universal |
| **WebP** | ~25–35% smaller | Both | Yes / No / Yes | Medium | Fast | Free (BSD), Google | All modern browsers |
| **AVIF** | ~40–55% smaller | Both (lossless is weak) | Yes / Yes / Yes | **Slow** | Medium | Royalty-free (AOMedia) | All modern browsers |
| **HEIC** | ~40–50% smaller | Lossy (lossless possible) | Yes / Yes / Yes | Medium (HW on phones) | Medium (HW) | **Patent-encumbered (HEVC)**, royalties | Apple native, spotty elsewhere, nearly no browsers |
| **JXL** | ~20–50% smaller; lossless JPEG recompression ~20% | Both (strong lossless) | Yes / Yes / Yes | Medium–fast | Fast | Royalty-free, open (BSD) | Safari, some others; Chrome dropped then re-added; patchy |

Numbers are rough and content-dependent.

## When to use what

- **JPEG**: safe default for photos, email, anything needing universal compatibility.
- **PNG**: screenshots, UI, logos, pixel art, anything with sharp edges needing lossless + transparency.
- **WebP**: pragmatic web default; good savings, cheap to encode, wide support.
- **AVIF**: best web delivery for photos at low bitrates, HDR. Pre-encode at build time because encoding is slow. Can look smooth and lose fine detail.
- **HEIC**: camera capture on iPhones. Convert to JPEG/AVIF/WebP for sharing and web.
- **JXL**: archival and master files, lossless JPEG recompression, high-quality photos, progressive decoding. Use it where you control the decoder; add a fallback on the web.

## TL;DR

- Web photos: AVIF, then WebP, then JPEG fallback via `<picture>`.
- Graphics needing lossless: PNG (or lossless WebP/JXL).
- Archive: JXL or PNG.
- Avoid HEIC outside Apple's ecosystem.
