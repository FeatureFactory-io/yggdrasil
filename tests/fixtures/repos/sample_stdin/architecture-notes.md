# Architecture notes

This system includes:

- **Payment API** — a Container in the Technology package that exposes HTTP payment endpoints
- **Order Domain** — a Component in the Application package for order business logic
- **Notification Service** — a Container that sends refund receipts

Focus on interface changes between Payment API and Notification Service.
