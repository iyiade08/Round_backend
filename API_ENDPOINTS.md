# Round Backend API Endpoints

Base URL for local development:

```text
http://127.0.0.1:8000/api/v1
```

Frontend should authenticate users with Firebase Auth first, then send the Firebase ID token to Django on every protected request.

All protected requests must include:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

## Authentication

### Create Or Sync Backend Session

Use this after Firebase registration or Firebase login. This endpoint verifies the Firebase token and creates/updates the matching Django user.

```http
POST /auth/session/
```

Full local URL:

```text
http://127.0.0.1:8000/api/v1/auth/session/
```

Headers:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

Body:

```json
{
  "full_name": "Test User",
  "phone_number": "",
  "location": "",
  "bio": "",
  "family_name": "",
  "house": "",
  "village": "",
  "clan": ""
}
```

Only `full_name` is needed for the first version. The other fields are optional.

Success response:

```json
{
  "id": "uuid",
  "firebase_uid": "firebase-user-id",
  "email": "test@example.com",
  "full_name": "Test User",
  "avatar_initials": "TU",
  "phone_number": "",
  "date_joined": "2026-07-02T12:00:00Z",
  "profile": {
    "location": "",
    "bio": "",
    "family_name": "",
    "house": "",
    "village": "",
    "clan": "",
    "join_date": "2026-07-02"
  }
}
```

### Get Current User

Use this when the frontend app loads or when protected pages need the logged-in profile.

```http
GET /auth/me/
```

Full local URL:

```text
http://127.0.0.1:8000/api/v1/auth/me/
```

Headers:

```http
Authorization: Bearer <firebase_id_token>
```

Success response:

```json
{
  "id": "uuid",
  "firebase_uid": "firebase-user-id",
  "email": "test@example.com",
  "full_name": "Test User",
  "avatar_initials": "TU",
  "phone_number": "",
  "date_joined": "2026-07-02T12:00:00Z",
  "profile": {
    "location": "",
    "bio": "",
    "family_name": "",
    "house": "",
    "village": "",
    "clan": "",
    "join_date": "2026-07-02"
  }
}
```

### Update Current User

Use this for profile editing.

```http
PATCH /auth/me/
```

Full local URL:

```text
http://127.0.0.1:8000/api/v1/auth/me/
```

Headers:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

Body:

```json
{
  "full_name": "Updated Name",
  "phone_number": "+2348000000000",
  "location": "Lagos, Nigeria",
  "bio": "Building bridges across communities.",
  "family_name": "Okafor",
  "house": "Nnenne",
  "village": "Umuahia",
  "clan": "Okafor"
}
```

All fields are optional.

### Request Password Reset Code

Use this when a user taps "Forgot password". This endpoint does not require Firebase authentication.

```http
POST /auth/password-reset/request/
```

Full local URL:

```text
http://127.0.0.1:8000/api/v1/auth/password-reset/request/
```

Headers:

```http
Content-Type: application/json
```

Body:

```json
{
  "email": "test@example.com",
  "code_type": "numeric"
}
```

`code_type` is optional. Allowed values:

```text
numeric, alphanumeric
```

Success response:

```json
{
  "detail": "If an account exists for this email, a reset code has been generated.",
  "email": "test@example.com",
  "code_type": "numeric",
  "code_length": 6,
  "expires_at": "2026-07-06T12:10:00Z",
  "expires_in_seconds": 600,
  "reset_code": "123456"
}
```

Notes:

- Numeric codes are 6 digits, for example `123456`.
- Alphanumeric codes are 6 uppercase letters/numbers, for example `A7K2Q9`.
- The code expires after 10 minutes.
- The backend stores only a hashed version of the code.
- For unknown emails, `reset_code` returns `null`.

### Confirm Password Reset

Use this after the user enters the reset code and their new password. This endpoint does not require Firebase authentication.

```http
POST /auth/password-reset/confirm/
```

Full local URL:

```text
http://127.0.0.1:8000/api/v1/auth/password-reset/confirm/
```

Headers:

```http
Content-Type: application/json
```

Body:

```json
{
  "email": "test@example.com",
  "code": "123456",
  "new_password": "newpassword123"
}
```

Success response:

```json
{
  "detail": "Password reset successful. The user can now log in with the new password.",
  "user": {
    "id": "uuid",
    "firebase_uid": "firebase-user-id",
    "email": "test@example.com",
    "full_name": "Test User",
    "avatar_initials": "TU",
    "phone_number": "",
    "date_joined": "2026-07-02T12:00:00Z",
    "profile": {
      "location": "",
      "bio": "",
      "family_name": "",
      "house": "",
      "village": "",
      "clan": "",
      "join_date": "2026-07-02"
    }
  }
}
```

This updates the user's Firebase Auth password using Firebase Admin, then updates the local Django password hash for consistency.

## Communities And Memberships

All community endpoints require:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

### List Visible Communities

Returns public active communities plus private communities where the current user is an active member.

```http
GET /communities/
```

Optional query params:

```text
?type=family
?search=okafor
```

Full local URL:

```text
http://127.0.0.1:8000/api/v1/communities/
```

### Create Community

Creates a community and automatically makes the current user the `owner`.

```http
POST /communities/
```

Body:

```json
{
  "name": "Okafor Family Circle",
  "type": "family",
  "description": "Extended family network.",
  "location": "Lagos, Nigeria",
  "visibility": "public",
  "color_key": "green",
  "banner_key": "green-gradient"
}
```

Allowed `type` values:

```text
church, mosque, neighborhood, school, family, professional, village, clan
```

Allowed `visibility` values:

```text
public, private, invite_only
```

Success response:

```json
{
  "id": "uuid",
  "name": "Okafor Family Circle",
  "slug": "okafor-family-circle",
  "type": "family",
  "description": "Extended family network.",
  "location": "Lagos, Nigeria",
  "visibility": "public",
  "status": "active",
  "color_key": "green",
  "banner_key": "green-gradient",
  "members_count": 1,
  "my_membership": {
    "id": "uuid",
    "role": "owner",
    "status": "active",
    "joined_at": "2026-07-02T12:00:00Z"
  },
  "created_by": {
    "id": "uuid",
    "email": "owner@example.com",
    "full_name": "Owner User",
    "avatar_initials": "OU"
  },
  "created_at": "2026-07-02T12:00:00Z",
  "updated_at": "2026-07-02T12:00:00Z"
}
```

### List My Communities

Returns communities where the current user has an active membership.

```http
GET /communities/my/
```

### Get Community Detail

```http
GET /communities/{community_id}/
```

Private and invite-only communities are visible only to active members.

### Update Community

Only community officers can update a community.

```http
PATCH /communities/{community_id}/
```

Body example:

```json
{
  "name": "Updated Community Name",
  "description": "Updated description.",
  "visibility": "private"
}
```

### List Community Members

```http
GET /communities/{community_id}/members/
```

Success response:

```json
[
  {
    "id": "uuid",
    "user": {
      "id": "uuid",
      "email": "member@example.com",
      "full_name": "Member User",
      "avatar_initials": "MU"
    },
    "role": "member",
    "status": "active",
    "joined_at": "2026-07-02T12:00:00Z",
    "contribution_total": "0.00",
    "created_at": "2026-07-02T12:00:00Z",
    "updated_at": "2026-07-02T12:00:00Z"
  }
]
```

### Join Or Request To Join Community

```http
POST /communities/{community_id}/join/
```

No body is required.

Behavior:

- `public` community: creates/activates membership with `status=active`.
- `private` or `invite_only` community: creates membership request with `status=requested`.

### Update Membership Role Or Status

Only community officers can update memberships.

```http
PATCH /community-memberships/{membership_id}/
```

Body:

```json
{
  "role": "treasurer",
  "status": "active"
}
```

Allowed `role` values:

```text
owner, president, secretary, treasurer, officer, member
```

Allowed `status` values:

```text
active, invited, requested, suspended, left
```

## Dashboard

All dashboard endpoints require:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

### Dashboard Summary

Use this to load the main dashboard counters and current user.

```http
GET /dashboard/summary/
```

Success response:

```json
{
  "user": {
    "id": "uuid",
    "firebase_uid": "firebase-user-id",
    "email": "test@example.com",
    "full_name": "Test User",
    "avatar_initials": "TU",
    "phone_number": "",
    "date_joined": "2026-07-02T12:00:00Z",
    "profile": {
      "location": "",
      "bio": "",
      "family_name": "",
      "house": "",
      "village": "",
      "clan": "",
      "join_date": "2026-07-02"
    }
  },
  "stats": {
    "connections": 3,
    "communities": 2,
    "events": 0,
    "contributions": "2500.00"
  },
  "savings": {},
  "investments": {}
}
```

### Dashboard Activity

Use this to show recent dashboard activity from community creation, joins, and join requests.

```http
GET /dashboard/activity/
```

Success response:

```json
[
  {
    "id": "membership-uuid",
    "type": "community_created",
    "title": "Created Okafor Family Circle",
    "description": "Extended family network.",
    "occurred_at": "2026-07-02T12:00:00Z",
    "community": {
      "id": "community-uuid",
      "name": "Okafor Family Circle",
      "slug": "okafor-family-circle",
      "type": "family",
      "description": "Extended family network.",
      "location": "Lagos, Nigeria",
      "visibility": "public",
      "color_key": "green",
      "banner_key": "green-gradient",
      "members_count": 1,
      "my_membership": {
        "id": "membership-uuid",
        "role": "owner",
        "status": "active",
        "joined_at": "2026-07-02T12:00:00Z",
        "contribution_total": "0.00"
      }
    }
  }
]
```

Activity `type` values currently returned:

```text
community_created, community_joined, community_join_requested
```

### Dashboard Payment Reminders

Use this for payment reminders. This returns an empty list until the finance/payment module is implemented.

```http
GET /dashboard/payment-reminders/
```

Success response:

```json
[]
```

### Dashboard My Communities

Use this for a compact dashboard list of the logged-in user's active communities.

```http
GET /dashboard/my-communities/
```

Success response:

```json
[
  {
    "id": "community-uuid",
    "name": "Okafor Family Circle",
    "slug": "okafor-family-circle",
    "type": "family",
    "description": "Extended family network.",
    "location": "Lagos, Nigeria",
    "visibility": "public",
    "color_key": "green",
    "banner_key": "green-gradient",
    "members_count": 1,
    "my_membership": {
      "id": "membership-uuid",
      "role": "owner",
      "status": "active",
      "joined_at": "2026-07-02T12:00:00Z",
      "contribution_total": "0.00"
    }
  }
]
```

### Dashboard Life Circle Map

Use this to draw the dashboard relationship map between the user and their communities.

```http
GET /dashboard/life-circle-map/
```

Success response:

```json
{
  "center": "user-uuid",
  "nodes": [
    {
      "id": "user-uuid",
      "type": "user",
      "label": "Test User",
      "avatar_initials": "TU"
    },
    {
      "id": "community-uuid",
      "type": "family",
      "label": "Okafor Family Circle",
      "location": "Lagos, Nigeria",
      "members_count": 1
    }
  ],
  "links": [
    {
      "source": "user-uuid",
      "target": "community-uuid",
      "relationship": "owner",
      "status": "active"
    }
  ]
}
```

## People, Connections, And Recommendations

All people and connection endpoints require:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

### List People

Use this to browse active users except the current logged-in user.

```http
GET /people/
```

Optional query params:

```text
?search=okafor
```

Success response:

```json
[
  {
    "id": "user-uuid",
    "email": "nnamdi@example.com",
    "full_name": "Nnamdi Okafor",
    "avatar_initials": "NO",
    "phone_number": "",
    "profile": {
      "location": "Lagos, Nigeria",
      "family_name": "Okafor",
      "house": "",
      "village": "Umuahia",
      "clan": "Aro"
    },
    "connection_status": "none"
  }
]
```

Possible `connection_status` values:

```text
none, connected, pending_sent, pending_received
```

### Get People Recommendations

Use this to suggest people based on same family name, clan, village, shared community, and mutual connections.

```http
GET /people/recommendations/
```

Success response:

```json
[
  {
    "user": {
      "id": "user-uuid",
      "email": "nnamdi@example.com",
      "full_name": "Nnamdi Okafor",
      "avatar_initials": "NO",
      "phone_number": "",
      "profile": {
        "location": "Lagos, Nigeria",
        "family_name": "Okafor",
        "house": "",
        "village": "Umuahia",
        "clan": "Aro"
      },
      "connection_status": "none"
    },
    "score": 90,
    "reasons": [
      "Same family name",
      "Same clan",
      "Same village",
      "Shared community: Okafor Family Circle"
    ]
  }
]
```

### Send Connection Request

```http
POST /connections/requests/
```

Body:

```json
{
  "receiver_id": "user-uuid",
  "message": "Let us connect."
}
```

`message` is optional.

Success response:

```json
{
  "id": "request-uuid",
  "sender": {},
  "receiver": {},
  "message": "Let us connect.",
  "status": "pending",
  "direction": "sent",
  "created_at": "2026-07-06T12:00:00Z",
  "updated_at": "2026-07-06T12:00:00Z",
  "responded_at": null
}
```

### List Connection Requests

Use this to list sent and received connection requests for the logged-in user.

```http
GET /connections/requests/
```

Optional query params:

```text
?status=pending
?direction=sent
?direction=received
```

Possible request `status` values:

```text
pending, accepted, rejected, cancelled
```

Possible `direction` values:

```text
sent, received
```

### Accept Connection Request

Only the receiver can accept a request.

```http
POST /connections/requests/{request_id}/accept/
```

No body is required.

Success response returns the created connection:

```json
{
  "id": "connection-uuid",
  "user": {
    "id": "other-user-uuid",
    "email": "ada@example.com",
    "full_name": "Ada Okafor",
    "avatar_initials": "AO",
    "phone_number": "",
    "profile": {
      "location": "",
      "family_name": "Okafor",
      "house": "",
      "village": "Umuahia",
      "clan": "Aro"
    },
    "connection_status": "connected"
  },
  "connected_at": "2026-07-06T12:00:00Z",
  "created_at": "2026-07-06T12:00:00Z",
  "updated_at": "2026-07-06T12:00:00Z"
}
```

### Reject Connection Request

Only the receiver can reject a request.

```http
POST /connections/requests/{request_id}/reject/
```

No body is required.

Success response returns the updated request with:

```json
{
  "status": "rejected"
}
```

### List My Connections

Use this to list accepted connections for the logged-in user.

```http
GET /connections/
```

Success response:

```json
[
  {
    "id": "connection-uuid",
    "user": {
      "id": "other-user-uuid",
      "email": "nnamdi@example.com",
      "full_name": "Nnamdi Okafor",
      "avatar_initials": "NO",
      "phone_number": "",
      "profile": {
        "location": "",
        "family_name": "Okafor",
        "house": "",
        "village": "Umuahia",
        "clan": "Aro"
      },
      "connection_status": "connected"
    },
    "connected_at": "2026-07-06T12:00:00Z",
    "created_at": "2026-07-06T12:00:00Z",
    "updated_at": "2026-07-06T12:00:00Z"
  }
]
```

### Remove Connection

Use this to remove an accepted connection.

```http
DELETE /connections/{connection_id}/
```

Success response:

```http
204 No Content
```

## Frontend Integration Notes

The frontend developer should:

1. Use Firebase Auth for registration and login.
2. Get the user ID token with Firebase, usually `firebaseUser.getIdToken()`.
3. Send that token in the `Authorization` header.
4. Call `POST /auth/session/` after registration or login.
5. Call `GET /auth/me/` on app load to restore the logged-in user.
6. If Django returns `401`, call `firebaseUser.getIdToken(true)` to force-refresh the token and retry once.

The Django backend cannot refresh Firebase ID tokens by itself. Token refresh must happen in the frontend because Firebase refresh tokens live in the browser Firebase SDK.

If login succeeds in Firebase but Django returns `401`, check these in order:

- Force refresh the token with `firebaseUser.getIdToken(true)` after login.
- Restart the frontend dev server after changing `.env.local`.
- Clear browser site data for `localhost:5173` if an old Firebase session is cached.
- Confirm the local computer date/time is correct and set automatically.
- Confirm the backend service account JSON belongs to the same Firebase project as the web app.

Minimal frontend request example:

```js
const token = await firebaseUser.getIdToken();

const response = await fetch("http://127.0.0.1:8000/api/v1/auth/me/", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const user = await response.json();
```

Token refresh example:

```js
async function apiRequest(path, options = {}) {
  let token = await firebaseUser.getIdToken();
  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (response.status === 401) {
    token = await firebaseUser.getIdToken(true);
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
  }

  return response;
}
```

## Current Backend Status

Implemented:

- Firebase Admin token verification
- Custom Django user model
- User profile model
- `POST /api/v1/auth/session/`
- `GET /api/v1/auth/me/`
- `PATCH /api/v1/auth/me/`
- `POST /api/v1/auth/password-reset/request/`
- `POST /api/v1/auth/password-reset/confirm/`
- Community and membership models
- `GET /api/v1/communities/`
- `POST /api/v1/communities/`
- `GET /api/v1/communities/my/`
- `GET /api/v1/communities/{community_id}/`
- `PATCH /api/v1/communities/{community_id}/`
- `GET /api/v1/communities/{community_id}/members/`
- `POST /api/v1/communities/{community_id}/join/`
- `PATCH /api/v1/community-memberships/{membership_id}/`
- `GET /api/v1/dashboard/summary/`
- `GET /api/v1/dashboard/activity/`
- `GET /api/v1/dashboard/payment-reminders/`
- `GET /api/v1/dashboard/my-communities/`
- `GET /api/v1/dashboard/life-circle-map/`
- `GET /api/v1/people/`
- `GET /api/v1/people/recommendations/`
- `POST /api/v1/connections/requests/`
- `GET /api/v1/connections/requests/`
- `POST /api/v1/connections/requests/{request_id}/accept/`
- `POST /api/v1/connections/requests/{request_id}/reject/`
- `GET /api/v1/connections/`
- `DELETE /api/v1/connections/{connection_id}/`

Next backend modules:

- Lineage
- Events
- Finance
- Marketplace
- Investments
