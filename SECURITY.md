# Security Policy

## Supported versions

Until the first public release, security fixes are made on the `main` branch. After `v1.0.0`, the latest published release and `main` will receive security fixes. Older releases are not guaranteed support unless explicitly listed here.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting feature:

1. Open the repository's **Security** tab.
2. Select **Advisories** and **Report a vulnerability**.
3. Include affected versions or commits, reproduction steps, impact, and any suggested mitigation.

If private vulnerability reporting is unavailable, contact the maintainer through the contact method on the GitHub profile and ask for a private security channel without including exploit details in the initial public message.

You should receive an acknowledgement within seven days. Triage and remediation timelines depend on severity and reproducibility. Please allow a reasonable remediation window before disclosure.

## Scope

Security-sensitive areas include local path authorization, source-image immutability, export destinations, symlinks, temporary files, cache cleanup, the loopback HTTP bridge, dependency integrity, and portable-build provenance.

FlatShot is designed to bind its bridge to loopback. Exposing it to a network, processing untrusted shared folders, or running a modified build may change the threat model.
