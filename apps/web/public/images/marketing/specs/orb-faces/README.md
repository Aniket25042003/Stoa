# Product Orb face assets

## Source files (manual generation)

Place raw exports in this folder as `1.jpeg` … `6.jpeg`:

| JPEG | Feature | Output WebP |
|------|---------|-------------|
| `1.jpeg` | ICP & Customer Research | `../orb-faces/01-icp-research.webp` |
| `2.jpeg` | Content Creation Bottleneck | `../orb-faces/02-content-bottleneck.webp` |
| `3.jpeg` | Competitive Intelligence | `../orb-faces/03-competitive-intel.webp` |
| `4.jpeg` | Campaign Analysis | `../orb-faces/04-campaign-analysis.webp` |
| `5.jpeg` | Sales–Marketing Alignment | `../orb-faces/05-gtm-alignment.webp` |
| `6.jpeg` | Campaign Launch Orchestration | `../orb-faces/06-launch-orchestration.webp` |

## Convert to WebP (from `apps/web/public/images/marketing`)

```bash
for i in 1 2 3 4 5 6; do
  case $i in
    1) name=01-icp-research ;;
    2) name=02-content-bottleneck ;;
    3) name=03-competitive-intel ;;
    4) name=04-campaign-analysis ;;
    5) name=05-gtm-alignment ;;
    6) name=06-launch-orchestration ;;
  esac
  cwebp -q 85 -resize 1536 0 "specs/orb-faces/$i.jpeg" -o "orb-faces/${name}.webp"
done
cwebp -q 85 -resize 1536 0 specs/orb-faces/1.jpeg -o orb-faces/orb-fallback.webp
```

Generate new faces with nano-banana-pro using the JSON specs in this folder.
