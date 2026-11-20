# Security

StarMap runs a small web server on `127.0.0.1` so your browser can draw the map. It is built to be safe on a shared or untrusted network:

- It listens on this computer only (`127.0.0.1`), never on the network.
- Every start creates a new random key. The browser receives it once, from the address StarMap opens, and keeps it in a cookie that other websites cannot send (`SameSite=Strict`, `HttpOnly`). Requests without it are refused.
- Requests are refused unless they name `127.0.0.1` or `localhost` as the host, which blocks DNS-rebinding attacks, and changes must come from the StarMap page itself.
- It only serves files inside your home folder, only of the types it can preview, and never as something the browser would run as part of StarMap.
- "Open file" refuses programs and scripts. "Move to Trash" only moves a copy after checking byte for byte that an identical copy is being kept, and it never deletes outright.

If you find a way around any of this, please open a private security advisory on GitHub (Security tab, "Report a vulnerability") instead of a public issue.
