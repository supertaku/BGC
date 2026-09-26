# Vercel deployment

The BGC viewer deploys from GitHub using Vercel's standard Next.js integration.

## Project settings

- Git repository: `supertaku/BGC`
- Root Directory: `web`
- Framework Preset: Next.js
- Build Command: `npm run build`
- Output Directory: framework default
- Required runtime assets: `web/public/models/`

The build runs `npm run verify:deploy` automatically through the `prebuild` script. Asset generation remains a local workflow; Vercel only verifies and serves committed runtime files.

No production environment variables are currently required. `NEXT_PUBLIC_SITE_URL` is optional metadata configuration and must be set in Vercel only if an explicit canonical site URL is wanted.

## Local production check

From `web/`:

```bash
npm ci
npm run verify:deploy
npm run build
npm run start
```

Open `http://localhost:3000` and verify the viewer, Explore, Search, Walk, Tour, and Graphics Settings. Check the browser console and network requests for required `.glb`, `.json`, `.png`, `.jpg`, and `.webp` files.

## Dashboard deployment

1. Open Vercel and select **Add New → Project**.
2. Import `supertaku/BGC` from GitHub.
3. Set **Root Directory** to `web`.
4. Confirm the **Next.js** framework preset.
5. Leave the install, build, and output settings at their framework defaults.
6. Deploy a preview and open its URL.
7. Verify `/world/bgc-world.json`, `/world/bgc-interactive.json`, and `/world/detail/m23/catalog.json`.
8. Verify representative GLBs from `/models/bgc/tiles/`, `/models/buildings/`, and `/models/m23r/tiles/` return HTTP 200.
9. Test the full viewer in a private window and confirm there are no required asset 404s or critical console errors.

Once the Vercel project is connected, pushes to the configured production branch trigger deployments automatically.
