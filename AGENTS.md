# Rules

## Builds
- All builds happen on Olex's PC. GitHub CI runs only lightweight checks (lint, quick tests); it never builds APKs, executables or other release files.
- Every file made by building, testing or running the program (build outputs, APKs, logs, screenshots, caches, virtual environments, downloads) goes inside the repo's `build/` folder, which is gitignored. Nothing like that goes anywhere else in the repo.
