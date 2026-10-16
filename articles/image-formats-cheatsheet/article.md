---
{
  "devto_id": 4858130,
  "title": "Image formats cheatsheet: JPEG, PNG, WebP, AVIF, JXL",
  "published": true,
  "description": "A quick comparison of JPEG, PNG, WebP, AVIF and JPEG XL: compression, speed, licensing and when to use each.",
  "tags": "webdev, images, performance, cheatsheet",
  "canonical_url": null,
  "main_image": null,
  "series": null,
  "organization_id": null
}
---

> **TL;DR**
>
> - Best compression: AVIF; JPEG XL
> - Best lossless compression: JPEG XL; WebP
> - As of 2026-10, JPEG XL only supported by Chrome and Firefox, not Safari
> - Stop using PNG, JPEG, because other formats just outperform them in every way

## Comparison

| Comparison field            | **JPEG**              | **PNG**                | **WebP**            | **AVIF**                | **JXL**                                                   |
| --------------------------- | --------------------- | ---------------------- | ------------------- | ----------------------- | --------------------------------------------------------- |
| Size vs JPEG (same quality) | baseline              | Much larger for photos | ~25–35% smaller     | ~40–55% smaller         | ~20–50% smaller; lossless JPEG recompression ~20%         |
| Lossy / Lossless            | Lossy (lossless rare) | Lossless               | Both                | Both (lossless is weak) | Both (strong lossless)                                    |
| Alpha / HDR / Anim          | No / No / No          | Yes / No / APNG        | Yes / No / Yes      | Yes / Yes / Yes         | Yes / Yes / Yes                                           |
| Encode                      | baseline              | Fast                   | Medium              | **Slow**                | Medium–fast                                               |
| Decode                      | baseline              | Fast                   | Fast                | Medium                  | Fast                                                      |
| License / patents           | Free, patents expired | Free, open             | Free (BSD), Google  | Royalty-free (AOMedia)  | Royalty-free, open (BSD)                                  |
| Support                     | Universal             | Universal              | All modern browsers | All modern browsers     | Safari, some others; Chrome dropped then re-added; patchy |

Numbers are rough and content-dependent.

## When to use what

- **JPEG**: safe default for photos, email, anything needing universal
  compatibility.
- **PNG**: screenshots, UI, logos, pixel art, anything with sharp edges needing
  lossless + transparency.
- **WebP**: pragmatic web default; good savings, cheap to encode, wide support.
- **AVIF**: best web delivery for photos at low bitrates, HDR. Pre-encode at
  build time because encoding is slow. Can look smooth and lose fine detail.
- **JXL**: archival and master files, lossless JPEG recompression, high-quality
  photos, progressive decoding. Use it where you control the decoder; add a
  fallback on the web.
