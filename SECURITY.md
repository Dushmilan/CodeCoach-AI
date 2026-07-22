# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability within CodeCoach AI, please send an email to **dushmilan05@gmail.com**. All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

## What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: Depends on severity, typically within 2 weeks

## Scope

### In Scope

- Authentication and authorization bypass
- SQL injection or data exposure
- Cross-site scripting (XSS) in the frontend
- Server-side request forgery (SSRF)
- Code execution vulnerabilities in the Piston integration
- API key exposure or leakage
- Any vulnerability that could compromise user data

### Out of Scope

- Denial of service attacks
- Social engineering
- Issues in third-party dependencies (report these upstream)
- Issues requiring physical access to a user's device

## Supported Versions

| Version  | Supported          |
| -------- | ------------------ |
| Latest   | :white_check_mark: |
| < Latest | :x:                |

## Security Best Practices for Contributors

When contributing to CodeCoach AI:

1. **Never commit secrets** - API keys, passwords, tokens must never be in code
2. **Validate input** - All user input must be validated on the backend
3. **Use parameterized queries** - Never interpolate user input into SQL
4. **Escape output** - Prevent XSS by escaping rendered content
5. **Follow dependency updates** - Keep dependencies current
6. **Use HTTPS** - All production deployments should use TLS

## Known Security Considerations

- **BYO API Key Model**: Users provide their own NVIDIA/Google API keys. These are stored in browser localStorage and proxied through the backend. Keys are never persisted server-side.
- **Piston Code Execution**: User code runs in an isolated Docker container. Network access is disabled (`PISTON_DISABLE_NETWORK_ACCESS=true`).
- **JWT Authentication**: Tokens use RS256 signing. Secret keys must be set via environment variables.

## Contact

- **Security email**: dushmilan05@gmail.com
- **GitHub Issues**: For non-security bugs only
