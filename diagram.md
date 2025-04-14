# OAuth 2.0 Authorization Code Flow

This diagram shows the full OAuth 2.0 **Authorization Code Grant** process, commonly used for web applications that authenticate users via a third-party provider.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Client (App)
    participant Authorization Server
    participant Resource Server

    User->>Client (App): Click "Login with OAuth"
    Client (App)->>Authorization Server: Redirect user with client_id
    Authorization Server->>User: Prompt for login & consent
    User->>Authorization Server: Login & grant access
    Authorization Server-->>Client (App): Redirect with authorization code
    Client (App)->>Authorization Server: Exchange code for access token
    Authorization Server-->>Client (App): Return access token
    Client (App)->>Resource Server: Request user data with access token
    Resource Server-->>Client (App): Return user data
    Client (App)-->>User: Show personalized content