# RAG Frontend - Next.js Application

A simple and elegant frontend for the RAG (Retrieval-Augmented Generation) backend built with Next.js, TypeScript, and Tailwind CSS.

## Features

- Clean, modern chat interface
- Real-time message display
- Dark mode support
- Responsive design
- Loading states and error handling
- Auto-scroll to latest messages

## Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000` (or configure different URL)

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env.local` file (optional - defaults to localhost:8000):

```bash
cp .env.example .env.local
```

Edit `.env.local` to configure your backend API URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run the Development Server

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm start
```

## Usage

1. Make sure your RAG backend is running at the configured URL
2. Open the frontend in your browser
3. Type your question in the input field at the bottom
4. Press Send or hit Enter to submit your question
5. The assistant will display the response from your RAG system

## Backend API Requirements

The frontend expects the backend to have the following endpoint:

**POST** `/ask`

Request body:
```json
{
  "question": "Your question here"
}
```

Response:
```json
{
  "answer": "The assistant's response",
  ...other fields are optional
}
```

## Customization

### Styling

The app uses Tailwind CSS for styling. You can customize colors, spacing, and other design elements in:
- `tailwind.config.ts` - Tailwind configuration
- `app/globals.css` - Global styles and CSS variables

### API Integration

To modify the API integration, edit the `handleSubmit` function in `app/page.tsx`.

## Project Structure

```
frontend/nextjs-app/
├── app/
│   ├── globals.css      # Global styles
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Main chat page
├── public/              # Static assets (if needed)
├── .env.example         # Environment variables example
├── next.config.ts       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Troubleshooting

### Backend Connection Issues

If you see "Please make sure the backend server is running" error:
1. Verify your backend is running
2. Check the API URL in `.env.local` matches your backend
3. Ensure CORS is configured on the backend to allow requests from `http://localhost:3000`

### TypeScript Errors

The TypeScript errors shown in the editor will resolve once you run `npm install`.

## License

This project is part of the RAG application suite.
