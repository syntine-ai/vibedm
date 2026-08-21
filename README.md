# Vibe DM Frontend

Welcome to the frontend repository for **Vibe DM**, the smart Instagram DM automation platform! This application is built using modern web technologies to provide a fast, responsive, and aesthetic user experience.

## Tech Stack

This project uses a robust, modern frontend stack:
- **Framework:** React 18
- **Build Tool:** Vite
- **Routing:** TanStack Router (File-based, type-safe routing)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Icons:** Lucide React
- **Data Fetching:** TanStack Query (React Query)
- **Language:** TypeScript

## Getting Started

### Prerequisites

Make sure you have [Node.js](https://nodejs.org/) installed on your machine.

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up your environment variables:
   Copy the `.env.example` file to `.env` and fill in the required values (like your Supabase keys and ngrok URL).
   ```bash
   cp .env.example .env
   ```

### Running Locally

Start the Vite development server:
```bash
npm run dev
```

The application will typically be available at `http://localhost:5173/` or `http://localhost:8080/`.

## Key Features

- **Modern Landing Page:** A sleek, aesthetic landing page optimized for conversions.
- **Secure Authentication:** User login and signup powered by Supabase and Instagram OAuth.
- **Automation Dashboard:** An intuitive interface to manage, create, and edit your Instagram DM automation flows.
- **Policy Pages:** Built-in Terms & Conditions, Privacy Policy, and Return/Refund Policies accessible from the footer.

## Project Structure

- `/src/routes` - All pages and routing components (managed by TanStack Router).
- `/src/components` - Reusable UI components (including shadcn/ui components).
- `/src/lib` - Utility functions and API hooks.
- `/src/integrations` - Third-party integrations (like Supabase client).

## License

© 2026 Syntine Labs. All rights reserved.
