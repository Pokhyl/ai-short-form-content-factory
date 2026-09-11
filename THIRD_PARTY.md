# Third-party components

## short-video-maker
- Upstream: https://github.com/gyoridavid/short-video-maker
- License: MIT
- Runtime image: `gyoridavid/short-video-maker:latest-tiny`
- Local compatibility override: container starts `node dist/index.js` directly because the published image's pnpm/Corepack entrypoint is currently broken.
